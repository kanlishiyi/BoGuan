"""
Agent 运行时管理
================
负责构建和缓存 DeepAgent 实例，管理对话线程和多轮上下文。
"""

import asyncio
import hashlib
import json
import os
import uuid
from typing import Callable, Dict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

from ..config import settings
from .tools import wrap_tools_with_retry


# ============================================================
# 全局状态
# ============================================================

#: 全局共享 checkpointer（即使 runtime 重建也不丢失对话状态）
shared_checkpointer = MemorySaver()

#: agent_id → runtime 缓存
_runtimes: Dict[str, dict] = {}

#: 当前会话中已建立上下文的 thread_id 集合
active_threads: set = set()

#: 每个 thread 的轮次计数器
thread_turns: Dict[str, int] = {}

#: agent_id → 当前活跃的 thread_id
agent_thread_map: Dict[str, str] = {}


# ============================================================
# 辅助函数
# ============================================================

def _cfg_hash(cfg: dict) -> str:
    """计算 Agent 配置的哈希值，用于判断是否需要重建 runtime。"""
    blob = json.dumps({
        "sp": cfg.get("system_prompt", ""),
        "sk": sorted(cfg.get("skills", [])),
        "mcp": cfg.get("mcp_servers", []),
        "llm": cfg.get("llm_config"),
    }, sort_keys=True)
    return hashlib.md5(blob.encode()).hexdigest()


def new_thread_id() -> str:
    """生成新的 thread_id。"""
    return f"t-{uuid.uuid4().hex[:8]}"


def restore_messages_from_history(messages: list, max_pairs: int = 10) -> list:
    """
    从保存的对话历史消息列表中恢复 LangChain 消息对象。

    只提取 user / ai 消息，限制最近 max_pairs 轮。

    Args:
        messages: 结构化消息列表 [{"t": "user", "text": "..."}, ...]
        max_pairs: 最大轮次

    Returns:
        LangChain Message 对象列表
    """
    pairs = []
    for m in messages:
        t = m.get("t")
        if t == "user":
            pairs.append(HumanMessage(content=m.get("text", "")))
        elif t == "ai":
            pairs.append(AIMessage(content=m.get("text", "")))

    if len(pairs) > max_pairs * 2:
        pairs = pairs[-(max_pairs * 2):]
    return pairs


def cleanup_thread(agent_id: str) -> None:
    """清理指定 Agent 关联的 thread 记录。"""
    old_tid = agent_thread_map.pop(agent_id, None)
    if old_tid:
        active_threads.discard(old_tid)
        thread_turns.pop(old_tid, None)


def invalidate_runtime(agent_id: str) -> None:
    """使指定 Agent 的 runtime 缓存失效。"""
    _runtimes.pop(agent_id, None)


# ============================================================
# 运行时构建
# ============================================================

async def build_runtime(
    cfg: dict,
    status_cb: Optional[Callable] = None,
) -> dict:
    """
    根据 Agent 配置构建或返回缓存的运行时。

    Args:
        cfg: Agent 配置字典（需包含 id, system_prompt, skills, mcp_servers 等）
        status_cb: 可选的异步回调函数，用于推送构建状态

    Returns:
        {"agent": CompiledGraph, "tools": [...], "n": int, "h": str}
    """
    aid = cfg["id"]
    h = _cfg_hash(cfg)

    # 命中缓存
    if aid in _runtimes and _runtimes[aid]["h"] == h:
        return _runtimes[aid]

    async def _s(msg: str):
        if status_cb:
            await status_cb(msg)

    await _s("正在初始化 Agent 运行时...")

    # 确保子进程使用 UTF-8 编码（Windows 兼容）
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # LLM
    lc = cfg.get("llm_config") or {}
    api_key = lc.get("api_key") or settings.ANTHROPIC_API_KEY
    base_url = lc.get("base_url") or settings.ANTHROPIC_BASE_URL
    model_name = lc.get("model") or settings.ANTHROPIC_MODEL
    print(f"  [runtime] LLM: model={model_name}, base_url={base_url}, key={api_key[:8]}...")

    llm = ChatAnthropic(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
        streaming=True,
    )

    # MCP 工具
    tools = []
    mcps = cfg.get("mcp_servers") or []
    if mcps:
        await _s(f"正在连接 {len(mcps)} 个 MCP 服务器...")
        sc = {
            s["name"]: {
                "url": s["url"],
                "transport": s.get("transport", "streamable_http"),
            }
            for s in mcps
        }
        print(f"  [runtime] MCP servers: {sc}")
        try:
            client = MultiServerMCPClient(sc)
            raw = await client.get_tools()
            tools = wrap_tools_with_retry(raw)
            tool_names = [t.name for t in tools[:10]]
            print(f"  [runtime] MCP 工具已加载: {len(tools)} 个, 前10: {tool_names}")
            await _s(f"已加载 {len(tools)} 个工具")
        except Exception as e:
            print(f"  [runtime] MCP 连接失败: {e}")
            await _s(f"MCP 连接警告: {e}")

    # Skills 路径
    sp = [
        f"skills/{s}/"
        for s in cfg.get("skills", [])
        if os.path.isdir(os.path.join(settings.SKILLS_DIR, s))
    ]
    print(f"  [runtime] Skills 路径: {sp}")

    # 构建 Agent
    root_dir = str(settings.SKILLS_DIR.parent)
    print(f"  [runtime] Backend root_dir: {root_dir}")
    backend = LocalShellBackend(
        root_dir=root_dir,
        inherit_env=True,
        virtual_mode=False,
    )
    prompt = cfg.get("system_prompt") or "你是一个智能助手。请用简体中文回复。"

    agent = create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt,
        skills=sp if sp else None,
        backend=backend,
        checkpointer=shared_checkpointer,
        name=f"agent-{aid[:8]}",
    )
    print(f"  [runtime] Agent 创建完成: tools={len(tools)}, skills={len(sp)}")

    rt = {"agent": agent, "tools": tools, "n": len(tools), "h": h}
    _runtimes[aid] = rt
    await _s(f"Agent 就绪（{len(tools)} 个工具）")
    return rt
