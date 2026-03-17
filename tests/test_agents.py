"""
Agent CRUD 测试
===============
验证 Agent 数据存储和查找逻辑。
"""

import json

from boguan.api.agents import _load, _save, find_agent


def test_load_empty(tmp_data_dir):
    """数据文件不存在时应返回空列表。"""
    result = _load()
    assert result == []


def test_save_and_load(tmp_data_dir, sample_agent):
    """保存后应能正确加载。"""
    _save([sample_agent])
    loaded = _load()
    assert len(loaded) == 1
    assert loaded[0]["id"] == sample_agent["id"]
    assert loaded[0]["name"] == sample_agent["name"]


def test_find_agent_exists(tmp_data_dir, sample_agent):
    """查找已存在的 Agent 应返回对应数据。"""
    _save([sample_agent])
    result = find_agent(sample_agent["id"])
    assert result is not None
    assert result["name"] == "测试 Agent"


def test_find_agent_not_exists(tmp_data_dir, sample_agent):
    """查找不存在的 Agent 应返回 None。"""
    _save([sample_agent])
    result = find_agent("nonexistent-id")
    assert result is None


def test_save_multiple_agents(tmp_data_dir, sample_agent):
    """应支持保存多个 Agent。"""
    agent2 = {**sample_agent, "id": "test-agent-002", "name": "第二个 Agent"}
    _save([sample_agent, agent2])
    loaded = _load()
    assert len(loaded) == 2
    assert find_agent("test-agent-002")["name"] == "第二个 Agent"
