"""
配置管理
========
从 .env 文件和环境变量中加载配置。
优先级：环境变量 > .env 文件 > 默认值

使用方式::

    from boguan.config import settings
    print(settings.ANTHROPIC_MODEL)
"""

import os
from pathlib import Path

# ------------------------------------------------------------------
# 项目根目录：包含 .env / skills/ / static/ 的目录
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------
# 加载 .env 文件（仅设置尚未存在的环境变量）
# ------------------------------------------------------------------
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value


class _Settings:
    """配置集合，所有属性均从环境变量读取，带默认值。"""

    # ---- LLM ----
    @property
    def ANTHROPIC_API_KEY(self) -> str:
        # 兼容 ANTHROPIC_API_KEY 和 ANTHROPIC_AUTH_TOKEN 两种环境变量名
        return os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN", "")

    @property
    def ANTHROPIC_BASE_URL(self) -> str:
        return os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

    @property
    def ANTHROPIC_MODEL(self) -> str:
        return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    # ---- MCP ----
    @property
    def MCP_SERVER_URL(self) -> str:
        return os.getenv("MCP_SERVER_URL", "http://localhost:10001/mcp")

    # ---- 端口 ----
    @property
    def PLATFORM_PORT(self) -> int:
        return int(os.getenv("PLATFORM_PORT", "8081"))

    @property
    def DEMO_PORT(self) -> int:
        return int(os.getenv("DEMO_PORT", "8080"))

    # ---- 安全 ----
    @property
    def DEFAULT_ADMIN_PASSWORD(self) -> str:
        return os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    # ---- 路径 ----
    @property
    def SKILLS_DIR(self) -> Path:
        return PROJECT_ROOT / "skills"

    @property
    def STATIC_DIR(self) -> Path:
        return PROJECT_ROOT / "static"

    @property
    def DATA_DIR(self) -> Path:
        p = PROJECT_ROOT / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def AGENTS_DATA_FILE(self) -> Path:
        return self.DATA_DIR / "agents.json"

    @property
    def USERS_DATA_FILE(self) -> Path:
        return self.DATA_DIR / "users.json"

    @property
    def HISTORY_DIR(self) -> Path:
        p = self.DATA_DIR / "chat_history"
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ---- 工具重试 ----
    @property
    def TOOL_MAX_RETRIES(self) -> int:
        return int(os.getenv("TOOL_MAX_RETRIES", "3"))

    @property
    def TOOL_RETRY_DELAY(self) -> float:
        return float(os.getenv("TOOL_RETRY_DELAY", "2.0"))

    # ---- PDF ----
    @property
    def PDF_FONT_DIR(self) -> str:
        return os.getenv("PDF_FONT_DIR", r"C:\Windows\Fonts")

    @property
    def PDF_FONT_REGULAR(self) -> str:
        return os.path.join(self.PDF_FONT_DIR, "msyh.ttc")

    @property
    def PDF_FONT_BOLD(self) -> str:
        return os.path.join(self.PDF_FONT_DIR, "msyhbd.ttc")

    @property
    def PDF_WATERMARK_TEXT(self) -> str:
        return os.getenv("PDF_WATERMARK_TEXT", "boguan")


# 全局单例
settings = _Settings()
