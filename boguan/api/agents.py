"""
Agent CRUD API
==============
Agent 的增删改查接口。
"""

import json
import os
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..config import settings
from ..models import AgentCreate, AgentUpdate
from ..core.runtime import cleanup_thread, invalidate_runtime
from .auth import require_auth

router = APIRouter(prefix="/api/agents", tags=["agents"])

# ============================================================
# 数据存储
# ============================================================

def _load() -> List[dict]:
    fp = settings.AGENTS_DATA_FILE
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save(agents: List[dict]):
    fp = settings.AGENTS_DATA_FILE
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)


def find_agent(agent_id: str) -> Optional[dict]:
    """根据 ID 查找 Agent。"""
    for a in _load():
        if a["id"] == agent_id:
            return a
    return None


def ensure_default_agent():
    """首次启动时创建默认 Agent。"""
    from ..config import settings as s
    agents = _load()
    if agents:
        return
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    default = {
        "id": "default-alert",
        "name": "告警分析助手",
        "description": "专注于监控数据分析和故障排查的智能运维助手",
        "avatar": "🔍",
        "system_prompt": (
            "你是一个专业的 IT 运维智能助手，专注于监控数据分析和故障排查。\n\n"
            "## 工作流程\n"
            "1. 先获取告警/问题的基本信息\n"
            "2. 结合 Skills 知识和可用工具制定分析计划\n"
            "3. 使用 write_todos 记录和更新计划\n"
            "4. 按计划逐步执行，每步完成后更新计划状态\n"
            "5. 最终输出完整的分析报告\n\n"
            "## 注意事项\n"
            "- 请始终用简体中文回复\n"
            "- 尽量在一次工具调用中获取足够信息\n"
            "- 对于不确定的结论，明确标注为'疑似'\n"
            "- 如果工具调用失败，调整计划继续执行"
        ),
        "skills": ["alert-analysis", "monitoring-assistant", "pdf-report"],
        "mcp_servers": [
            {"name": "monitoring", "url": s.MCP_SERVER_URL, "transport": "streamable_http"}
        ],
        "llm_config": None,
        "created_at": now,
        "updated_at": now,
    }
    _save([default])
    print(f"[启动] 已创建默认 Agent: {default['name']}")


# ============================================================
# 路由
# ============================================================

@router.get("")
async def list_agents(user: dict = Depends(require_auth)):
    """获取所有 Agent 列表。"""
    return _load()


@router.post("")
async def create_agent(body: AgentCreate, user: dict = Depends(require_auth)):
    """创建新 Agent。"""
    agents = _load()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    a = {
        "id": uuid.uuid4().hex[:12],
        **body.dict(),
        "mcp_servers": [s.dict() for s in body.mcp_servers],
        "created_at": now,
        "updated_at": now,
    }
    agents.append(a)
    _save(agents)
    return a


@router.put("/{aid}")
async def update_agent(aid: str, body: AgentUpdate, user: dict = Depends(require_auth)):
    """更新 Agent 配置。"""
    agents = _load()
    for i, a in enumerate(agents):
        if a["id"] == aid:
            d = body.dict()
            d["mcp_servers"] = [
                s.dict() if hasattr(s, "dict") else s
                for s in d.get("mcp_servers", [])
            ]
            a.update(d)
            a["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            agents[i] = a
            _save(agents)
            invalidate_runtime(aid)
            return a
    raise HTTPException(404, "Agent 不存在")


@router.delete("/{aid}")
async def delete_agent(aid: str, user: dict = Depends(require_auth)):
    """删除 Agent 及其关联数据。"""
    agents = _load()
    n = [a for a in agents if a["id"] != aid]
    if len(n) == len(agents):
        raise HTTPException(404)
    _save(n)
    invalidate_runtime(aid)
    cleanup_thread(aid)

    # 删除对话历史
    from .history import _history_path
    fp = _history_path(aid)
    if os.path.exists(fp):
        os.remove(fp)

    return {"ok": True}
