"""
Pydantic 数据模型
=================
API 请求/响应使用的数据结构定义。
"""

from typing import List, Optional

from pydantic import BaseModel


class MCPServer(BaseModel):
    """MCP 服务器配置。"""
    name: str
    url: str
    transport: str = "streamable_http"


class AgentCreate(BaseModel):
    """创建 Agent 的请求体。"""
    name: str
    description: str = ""
    avatar: str = "🤖"
    system_prompt: str = ""
    skills: List[str] = []
    mcp_servers: List[MCPServer] = []
    llm_config: Optional[dict] = None


class AgentUpdate(AgentCreate):
    """更新 Agent 的请求体（与创建相同结构）。"""
    pass


class LoginBody(BaseModel):
    """登录请求体。"""
    username: str
    password: str
