"""
环境快速验证
============
验证 LLM 连接、MCP 工具加载和 Agent 创建是否正常，不执行实际分析。

使用方法::

    python examples/quick_test.py
"""

import asyncio
import os
import sys

# 确保能找到项目根目录下的 boguan 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from boguan.config import settings


async def main():
    print("=" * 60)
    print("  博观 Agent 平台 - 环境快速验证")
    print("=" * 60)

    # 1. 配置检查
    print(f"\n[1/4] 检查配置...")
    print(f"  LLM 模型:   {settings.ANTHROPIC_MODEL}")
    print(f"  LLM 地址:   {settings.ANTHROPIC_BASE_URL}")
    print(f"  API Key:    {'已配置 (' + settings.ANTHROPIC_API_KEY[:8] + '...)' if settings.ANTHROPIC_API_KEY else '❌ 未配置'}")
    print(f"  MCP 地址:   {settings.MCP_SERVER_URL}")

    if not settings.ANTHROPIC_API_KEY:
        print("\n❌ 请先在 .env 文件中配置 ANTHROPIC_API_KEY")
        return

    # 2. Skill 发现
    print(f"\n[2/4] 扫描 Skills...")
    from boguan.core.skills import discover_skills
    skills = discover_skills()
    if skills:
        for s in skills:
            print(f"  ✓ {s['id']}: {s['description']}")
    else:
        print("  ⚠ 未发现任何 Skill")

    # 3. MCP 工具加载
    print(f"\n[3/4] 连接 MCP 服务器...")
    os.environ.setdefault("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY)

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        client = MultiServerMCPClient({
            "test": {"url": settings.MCP_SERVER_URL, "transport": "streamable_http"}
        })
        tools = await client.get_tools()
        print(f"  ✓ 已加载 {len(tools)} 个工具")
        if tools:
            for t in tools[:5]:
                desc = (t.description or "")[:40]
                print(f"    - {t.name}: {desc}")
            if len(tools) > 5:
                print(f"    ... 共 {len(tools)} 个")
    except Exception as e:
        print(f"  ⚠ MCP 连接失败: {e}")
        tools = []

    # 4. Agent 创建测试
    print(f"\n[4/4] 测试 Agent 创建...")
    try:
        from langchain_anthropic import ChatAnthropic
        from deepagents import create_deep_agent
        from deepagents.backends import LocalShellBackend
        from langgraph.checkpoint.memory import MemorySaver

        llm = ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            base_url=settings.ANTHROPIC_BASE_URL,
            api_key=settings.ANTHROPIC_API_KEY,
            streaming=True,
        )
        backend = LocalShellBackend(
            root_dir=str(settings.SKILLS_DIR.parent),
            inherit_env=True,
            virtual_mode=False,
        )
        agent = create_deep_agent(
            model=llm,
            tools=tools[:3] if tools else [],
            system_prompt="测试",
            backend=backend,
            checkpointer=MemorySaver(),
            name="test-agent",
        )
        print(f"  ✓ Agent 创建成功")
    except Exception as e:
        print(f"  ❌ Agent 创建失败: {e}")

    print(f"\n{'=' * 60}")
    print("  验证完成！")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
