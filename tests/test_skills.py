"""
Skill 发现测试
==============
验证 Skills 目录扫描功能。
"""

import os

from boguan.core.skills import discover_skills


def test_discover_from_empty_dir(tmp_path):
    """空目录应返回空列表。"""
    assert discover_skills(tmp_path) == []


def test_discover_nonexistent_dir(tmp_path):
    """不存在的目录应返回空列表。"""
    assert discover_skills(tmp_path / "no-such-dir") == []


def test_discover_valid_skill(tmp_path):
    """应正确解析 SKILL.md 元数据。"""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: 测试技能\n---\n# 内容\n",
        encoding="utf-8",
    )
    result = discover_skills(tmp_path)
    assert len(result) == 1
    assert result[0]["id"] == "my-skill"
    assert result[0]["description"] == "测试技能"


def test_discover_skill_without_description(tmp_path):
    """缺少 description 时应返回空字符串。"""
    skill_dir = tmp_path / "no-desc"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: no-desc\n---\n# 内容\n",
        encoding="utf-8",
    )
    result = discover_skills(tmp_path)
    assert len(result) == 1
    assert result[0]["description"] == ""


def test_discover_skips_non_skill_dirs(tmp_path):
    """没有 SKILL.md 的子目录应被跳过。"""
    (tmp_path / "not-a-skill").mkdir()
    (tmp_path / "random-file.txt").write_text("hello")
    assert discover_skills(tmp_path) == []
