"""
列出 MCP 服务器上所有可用工具
==============================
快速查看指定 MCP 服务器提供的工具列表。

使用方法::

    python examples/list_mcp_tools.py
    python examples/list_mcp_tools.py http://your-mcp-server/mcp
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from boguan.config import settings


async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else settings.MCP_SERVER_URL
    print(f"连接 MCP 服务器: {url}\n")

    from langchain_mcp_adapters.client import MultiServerMCPClient
    client = MultiServerMCPClient(
        {"server": {"url": url, "transport": "streamable_http"}}
    )
    tools = await client.get_tools()
    print(f"共 {len(tools)} 个工具:\n")

    for i, t in enumerate(tools, 1):
        desc = (t.description or "无描述").split("\n")[0][:60]
        print(f"  {i:3d}. {t.name}")
        print(f"       {desc}")

    print(f"\n共 {len(tools)} 个工具。")


if __name__ == "__main__":
    asyncio.run(main())
