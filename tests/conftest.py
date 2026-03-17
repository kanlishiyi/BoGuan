"""
pytest 全局 Fixtures
====================
为测试提供公共的 fixtures 和辅助工具。
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# 确保 boguan 包可以被导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 设置测试环境变量（在导入 boguan 之前）
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("MCP_SERVER_URL", "http://localhost:9999/mcp")


@pytest.fixture()
def tmp_data_dir(tmp_path, monkeypatch):
    """提供一个临时数据目录，避免污染真实数据。"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    history_dir = data_dir / "chat_history"
    history_dir.mkdir()

    # 让 settings 使用临时目录
    from boguan.config import settings

    monkeypatch.setattr(type(settings), "DATA_DIR", property(lambda self: data_dir))
    monkeypatch.setattr(
        type(settings), "AGENTS_DATA_FILE", property(lambda self: data_dir / "agents.json")
    )
    monkeypatch.setattr(
        type(settings), "USERS_DATA_FILE", property(lambda self: data_dir / "users.json")
    )
    monkeypatch.setattr(
        type(settings), "HISTORY_DIR", property(lambda self: history_dir)
    )

    return data_dir


@pytest.fixture()
def sample_agent():
    """返回一个示例 Agent 字典。"""
    return {
        "id": "test-agent-001",
        "name": "测试 Agent",
        "description": "用于单元测试的 Agent",
        "avatar": "🧪",
        "system_prompt": "你是一个测试助手。",
        "skills": ["alert-analysis"],
        "mcp_servers": [
            {"name": "test-mcp", "url": "http://localhost:9999/mcp", "transport": "streamable_http"}
        ],
        "llm_config": None,
        "created_at": "2026-01-01 00:00:00",
        "updated_at": "2026-01-01 00:00:00",
    }


@pytest.fixture()
def sample_agents_file(tmp_data_dir, sample_agent):
    """在临时目录中创建一个包含示例 Agent 的 JSON 文件。"""
    fp = tmp_data_dir / "agents.json"
    with open(fp, "w", encoding="utf-8") as f:
        json.dump([sample_agent], f, ensure_ascii=False, indent=2)
    return fp
