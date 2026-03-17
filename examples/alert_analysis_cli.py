"""
CLI 告警分析演示
================
在命令行中运行 Agent 进行告警分析，展示 DeepAgents + Skills + MCP 的完整能力。

使用方法::

    python examples/alert_analysis_cli.py 488197
    python examples/alert_analysis_cli.py --alert-id 488197
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from boguan.config import settings

os.environ.setdefault("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY)


async def main(alert_id: str):
    print(f"\n{'='*60}")
    print(f"  博观 Agent - CLI 告警分析")
    print(f"  告警 ID: {alert_id}")
    print(f"{'='*60}\n")

    from langchain_anthropic import ChatAnthropic
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.checkpoint.memory import MemorySaver

    from deepagents import create_deep_agent
    from deepagents.backends import LocalShellBackend

    from boguan.core.tools import wrap_tools_with_retry

    # LLM
    llm = ChatAnthropic(
        model=settings.ANTHROPIC_MODEL,
        base_url=settings.ANTHROPIC_BASE_URL,
        api_key=settings.ANTHROPIC_API_KEY,
        streaming=True,
    )

    # MCP 工具
    print("[1/3] 加载 MCP 工具...")
    client = MultiServerMCPClient(
        {"monitoring": {"url": settings.MCP_SERVER_URL, "transport": "streamable_http"}}
    )
    raw_tools = await client.get_tools()
    tools = wrap_tools_with_retry(raw_tools)
    print(f"  已加载 {len(tools)} 个工具\n")

    # Agent
    print("[2/3] 创建 Agent...")
    backend = LocalShellBackend(
        root_dir=str(settings.SKILLS_DIR.parent),
        inherit_env=True,
        virtual_mode=False,
    )

    system_prompt = (
        "你是一个专业的 IT 运维智能助手，专注于监控数据分析和故障排查。\n\n"
        "## 工作流程\n"
        "1. 先获取告警的基本信息\n"
        "2. 结合 Skills 知识和可用工具制定分析计划\n"
        "3. 使用 write_todos 记录和更新计划\n"
        "4. 按计划逐步执行，每步完成后更新计划状态\n"
        "5. 最终输出完整的分析报告\n\n"
        "请始终使用简体中文回复。"
    )

    skill_dirs = [
        f"/skills/{d}/"
        for d in ["alert-analysis", "monitoring-assistant", "pdf-report"]
        if os.path.isdir(os.path.join(settings.SKILLS_DIR, d))
    ]

    agent = create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        skills=skill_dirs if skill_dirs else None,
        backend=backend,
        checkpointer=MemorySaver(),
        name="alert-analyzer",
    )
    print("  Agent 就绪\n")

    # 执行分析
    print("[3/3] 开始分析...\n")
    print("-" * 60)

    query = (
        f"请帮我分析告警ID为 {alert_id} 的告警。\n"
        f"请严格按照工作流程执行：\n"
        f"1. 先调用 get_alert_by_id 获取告警基本信息\n"
        f"2. 根据告警的实际情况，使用 write_todos 制定分析计划\n"
        f"3. 按计划逐步执行，每步完成后更新计划状态\n"
        f"4. 最终输出完整的分析报告"
    )

    config = {"configurable": {"thread_id": "cli-demo"}, "recursion_limit": 80}

    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": query}]},
        config=config,
        version="v2",
    ):
        kind = event.get("event", "")
        name = event.get("name", "")
        data = event.get("data", {})

        if kind == "on_chat_model_stream":
            chunk = data.get("chunk")
            if not chunk:
                continue
            content = getattr(chunk, "content", "")
            if isinstance(content, str) and content:
                print(content, end="", flush=True)
            elif isinstance(content, list):
                for b in content:
                    if isinstance(b, dict):
                        if b.get("type") == "text" and b.get("text"):
                            print(b["text"], end="", flush=True)
                        elif b.get("type") == "thinking" and b.get("thinking"):
                            print(f"\n💭 {b['thinking'][:100]}...", flush=True)

        elif kind == "on_chat_model_end":
            output = data.get("output")
            if output:
                for tc in getattr(output, "tool_calls", []):
                    print(f"\n\n🔧 调用工具: {tc['name']}")

        elif kind == "on_tool_end" and name != "write_todos":
            output = data.get("output")
            if output:
                r = str(getattr(output, "content", str(output)))
                if len(r) > 200:
                    r = r[:200] + "..."
                print(f"  ✓ {name}: {r}")

    print(f"\n{'='*60}")
    print("  分析完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLI 告警分析演示")
    parser.add_argument("alert_id", nargs="?", default="488197", help="告警 ID")
    parser.add_argument("--alert-id", dest="alert_id_opt", help="告警 ID（可选格式）")
    args = parser.parse_args()

    aid = args.alert_id_opt or args.alert_id
    asyncio.run(main(aid))
