"""
Skill 知识库发现
================
扫描 skills/ 目录，解析 SKILL.md 文件中的元数据。
"""

import os
import re
from pathlib import Path
from typing import List

from ..config import settings


def discover_skills(skills_dir: Path | None = None) -> List[dict]:
    """
    扫描技能目录，返回可用技能列表。

    每个技能目录下需包含 ``SKILL.md`` 文件，文件头需有 YAML Front Matter::

        ---
        name: alert-analysis
        description: 告警分析技能
        ---

    Args:
        skills_dir: 技能目录路径，默认使用配置中的 SKILLS_DIR

    Returns:
        [{"id": "alert-analysis", "name": "alert-analysis", "description": "..."}]
    """
    skills_dir = skills_dir or settings.SKILLS_DIR
    result: list[dict] = []

    if not os.path.isdir(skills_dir):
        return result

    for name in sorted(os.listdir(skills_dir)):
        fp = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.isfile(fp):
            continue
        desc = ""
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
            m = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
            if m:
                desc = m.group(1).strip()
        result.append({"id": name, "name": name, "description": desc})

    return result
