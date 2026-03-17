"""
配置模块测试
============
验证 boguan.config 的行为。
"""

import os


def test_settings_singleton():
    """settings 应为全局单例。"""
    from boguan.config import settings as s1
    from boguan.config import settings as s2
    assert s1 is s2


def test_settings_defaults():
    """未设置环境变量时应返回默认值。"""
    from boguan.config import settings

    assert settings.PLATFORM_PORT == int(os.getenv("PLATFORM_PORT", "8081"))
    assert settings.TOOL_MAX_RETRIES == int(os.getenv("TOOL_MAX_RETRIES", "3"))
    assert settings.TOOL_RETRY_DELAY == float(os.getenv("TOOL_RETRY_DELAY", "2.0"))


def test_settings_env_override(monkeypatch):
    """环境变量应覆盖默认值。"""
    from boguan.config import settings

    monkeypatch.setenv("PLATFORM_PORT", "9999")
    assert settings.PLATFORM_PORT == 9999

    monkeypatch.setenv("TOOL_MAX_RETRIES", "5")
    assert settings.TOOL_MAX_RETRIES == 5


def test_project_root():
    """PROJECT_ROOT 应指向包含 boguan/ 目录的上层。"""
    from boguan.config import PROJECT_ROOT
    assert (PROJECT_ROOT / "boguan").is_dir()
