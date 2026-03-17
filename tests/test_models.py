"""
数据模型测试
============
验证 Pydantic 模型的校验和序列化行为。
"""

import pytest
from boguan.models import MCPServer, AgentCreate, AgentUpdate, LoginBody


class TestMCPServer:

    def test_default_transport(self):
        s = MCPServer(name="test", url="http://localhost:9999/mcp")
        assert s.transport == "streamable_http"

    def test_custom_transport(self):
        s = MCPServer(name="test", url="http://localhost:9999/mcp", transport="sse")
        assert s.transport == "sse"


class TestAgentCreate:

    def test_minimal(self):
        a = AgentCreate(name="测试Agent")
        assert a.name == "测试Agent"
        assert a.description == ""
        assert a.avatar == "🤖"
        assert a.skills == []
        assert a.mcp_servers == []
        assert a.llm_config is None

    def test_full(self):
        a = AgentCreate(
            name="完整Agent",
            description="一段描述",
            avatar="🔍",
            system_prompt="你是助手",
            skills=["s1", "s2"],
            mcp_servers=[MCPServer(name="m1", url="http://x/mcp")],
            llm_config={"model": "test"},
        )
        assert len(a.mcp_servers) == 1
        assert a.llm_config["model"] == "test"


class TestAgentUpdate:

    def test_inherits_agent_create(self):
        """AgentUpdate 应与 AgentCreate 拥有相同字段。"""
        a = AgentUpdate(name="更新Agent")
        assert a.name == "更新Agent"


class TestLoginBody:

    def test_valid(self):
        body = LoginBody(username="admin", password="pass123")
        assert body.username == "admin"

    def test_missing_field(self):
        with pytest.raises(Exception):
            LoginBody(username="admin")  # password 缺失
