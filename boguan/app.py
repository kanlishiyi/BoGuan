"""
博观 Agent 管理平台 - FastAPI 应用入口
======================================
整合所有 API 路由，提供 Web 界面和 API 服务。

启动方式::

    # 方式一：直接运行
    python -m boguan.app

    # 方式二：使用 pyproject.toml 注册的命令
    boguan-platform

    浏览器访问 http://localhost:8081
"""

import os
import sys

# 修复 Windows 控制台编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse

from .config import settings

# 设置 API Key 环境变量（部分库从环境变量读取）
os.environ.setdefault("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY)

from .api import auth, agents, chat, history
from .api.auth import ensure_default_user
from .api.agents import ensure_default_agent
from .core.skills import discover_skills

# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(
    title="博观 Agent 管理平台",
    description="基于 DeepAgents 框架的 Agent 全生命周期管理与智能对话平台",
    version="1.0.0",
)

# 注册路由
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(chat.router)
app.include_router(history.router)


# ============================================================
# 附加 API（Skill / MCP 探测 / 配置默认值）
# ============================================================

from fastapi import Depends
from .api.auth import require_auth
from .models import MCPServer
from langchain_mcp_adapters.client import MultiServerMCPClient


@app.get("/api/skills")
async def api_skills(user: dict = Depends(require_auth)):
    """获取所有可用的 Skill 列表。"""
    return discover_skills()


@app.post("/api/mcp/probe")
async def probe_mcp(body: MCPServer, user: dict = Depends(require_auth)):
    """测试 MCP 服务器连接。"""
    try:
        c = MultiServerMCPClient(
            {body.name: {"url": body.url, "transport": body.transport}}
        )
        tools = await c.get_tools()
        return {
            "ok": True,
            "count": len(tools),
            "tools": [{"name": t.name, "desc": (t.description or "")[:60]} for t in tools],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/config/defaults")
async def defaults(user: dict = Depends(require_auth)):
    """获取默认配置值。"""
    return {
        "model": settings.ANTHROPIC_MODEL,
        "base_url": settings.ANTHROPIC_BASE_URL,
        "mcp_url": settings.MCP_SERVER_URL,
    }


# ============================================================
# 页面路由
# ============================================================

_NO_CACHE = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
}


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return FileResponse(
        os.path.join(settings.STATIC_DIR, "login.html"),
        headers=_NO_CACHE,
    )


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(
        os.path.join(settings.STATIC_DIR, "platform.html"),
        headers=_NO_CACHE,
    )


# ============================================================
# 启动事件
# ============================================================

@app.on_event("startup")
async def startup():
    ensure_default_user()
    ensure_default_agent()

    sk = discover_skills()
    print(f"[启动] 可用 Skills: {', '.join(s['id'] for s in sk)}")
    print(f"[启动] 博观 Agent 管理平台已就绪 → http://localhost:{settings.PLATFORM_PORT}")


# ============================================================
# 入口
# ============================================================

def main():
    """uvicorn 启动入口（供 pyproject.toml scripts 调用）。"""
    import uvicorn
    uvicorn.run(
        "boguan.app:app",
        host="0.0.0.0",
        port=settings.PLATFORM_PORT,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
