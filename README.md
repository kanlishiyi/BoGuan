<p align="center">
  <img src="docs/assets/logo.svg" width="80" alt="BoGuan Logo">
</p>

<h1 align="center">BoGuan</h1>

<p align="center">
  <strong>基于 <a href="https://github.com/langchain-ai/deepagents">DeepAgents</a> 框架的智能运维 Agent 管理与对话系统</strong>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> •
  <a href="#功能特性">功能特性</a> •
  <a href="#系统架构">系统架构</a> •
  <a href="#配置说明">配置说明</a> •
  <a href="#开发指南">开发指南</a> •
  <a href="LICENSE">License</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/framework-DeepAgents-green" alt="DeepAgents">
  <img src="https://img.shields.io/badge/protocol-MCP-purple" alt="MCP">
  <img src="https://img.shields.io/badge/license-Apache%202.0-orange" alt="License">
</p>

---

## 📖 项目简介

**BoGuan** 是一个开箱即用的 AI Agent 管理系统，基于 [DeepAgents](https://github.com/langchain-ai/deepagents) 框架构建，融合了 **Skills（技能知识库）** 和 **MCP（Model Context Protocol）** 两大核心能力，让 AI Agent 既有专业"大脑"又有可操作的"双手"。

项目面向 **IT 运维**、**智能监控**、**告警分析** 等场景，提供了一套完整的全栈解决方案：从 Agent 配置管理、多轮对话、工具调用可视化，到 PDF 报告生成。

## ✨ 功能特性

### 🤖 Agent 全生命周期管理
- **增删改查**：通过 Web UI 创建、编辑、删除 Agent
- **灵活配置**：自定义 System Prompt、Skills、MCP 工具源
- **热更新**：修改配置后无需重启，自动重建 Agent 运行时

### 🧠 Skills 技能知识库
- 基于 Markdown 定义领域知识和工作流程
- 内置告警分析、监控助手、PDF 报告等技能模板
- 支持自定义扩展，只需在 `skills/` 目录下创建新技能

### 🔌 MCP 工具协议
- 通过 [MCP](https://modelcontextprotocol.io/) 标准协议连接外部工具和数据源
- 支持多个 MCP 服务器同时接入
- 内置工具重试机制（失败自动重试，超过阈值跳过继续执行）
- Web UI 支持一键测试 MCP 连接

### 💬 智能对话
- **多轮对话**：支持上下文感知的持续交互，自动维护对话线程
- **流式输出**：SSE 实时推送思考过程、工具调用、AI 回复
- **对话持久化**：自动保存对话历史，重新进入自动加载
- **服务重启恢复**：服务重启后自动从历史恢复对话上下文

### 📊 PDF 报告生成
- 自动将分析结果转为结构化 PDF 文档
- 支持中文字体、自定义水印
- 包含告警概要、影响范围、排查过程、根因分析、处理建议等章节

### 🔐 用户认证
- 基于 Token 的登录认证
- 默认管理员账号，支持自定义密码

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    前端 Web UI                       │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ 登录页面  │  │Agent 管理│  │   对话界面 (SSE)  │  │
│  └──────────┘  └──────────┘  └───────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────┴──────────────────────────────┐
│                FastAPI 后端服务                       │
│  ┌──────┐ ┌────────┐ ┌──────┐ ┌─────────┐ ┌──────┐ │
│  │ Auth │ │ Agents │ │ Chat │ │ History │ │ PDF  │ │
│  └──────┘ └────────┘ └──┬───┘ └─────────┘ └──────┘ │
└─────────────────────────┼───────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────┐
│              DeepAgents 运行时                        │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ LLM 模型  │  │ Skills 知识库 │  │ MCP 工具调用  │  │
│  │(Anthropic)│  │ (Markdown)   │  │  (外部服务)   │  │
│  └──────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
BoGuan/
├── boguan/                    # 核心 Python 包
│   ├── __init__.py
│   ├── app.py                 # FastAPI 应用入口
│   ├── config.py              # 配置管理 (.env + 环境变量)
│   ├── models.py              # Pydantic 数据模型
│   ├── api/                   # API 路由模块
│   │   ├── auth.py            # 认证 (登录/登出)
│   │   ├── agents.py          # Agent CRUD
│   │   ├── chat.py            # 对话 SSE 流
│   │   └── history.py         # 对话历史持久化
│   └── core/                  # 核心业务逻辑
│       ├── runtime.py         # Agent 运行时管理
│       ├── tools.py           # 工具重试与中文名映射
│       ├── skills.py          # Skill 知识库发现
│       └── pdf.py             # PDF 报告生成器
├── static/                    # 前端静态文件
│   ├── platform.html          # Agent 管理平台主页面
│   └── login.html             # 登录页面
├── skills/                    # 技能知识库 (Markdown)
│   ├── alert-analysis/        # 告警分析技能
│   ├── monitoring-assistant/  # 监控助手技能
│   └── pdf-report/            # PDF 报告生成技能
├── examples/                  # 示例脚本
│   ├── quick_test.py          # 环境快速验证
│   ├── list_mcp_tools.py      # 列出 MCP 工具
│   └── alert_analysis_cli.py  # CLI 告警分析演示
├── tests/                     # 测试用例
├── docs/                      # 文档
├── .env.example               # 环境变量模板
├── pyproject.toml             # Python 项目配置
├── requirements.txt           # pip 依赖列表
├── Dockerfile                 # Docker 镜像构建
├── docker-compose.yml         # Docker Compose 编排
├── LICENSE                    # Apache 2.0 开源协议
└── README.md                  # 本文件
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 一个可用的 LLM API（Anthropic Claude 或兼容接口）
- （可选）MCP 服务器（用于外部工具调用）

### 方式一：直接运行

```bash
# 1. 克隆项目
git clone https://github.com/kanlishiyi/BoGuan.git
cd BoGuan

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\Activate.ps1     # Windows PowerShell

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key 和配置

# 5. 启动服务
python -m boguan.app
```

服务启动后访问 **http://localhost:8081**，默认管理员账号：`admin` / `admin123`

### 方式二：Docker 部署

```bash
# 1. 克隆并配置
git clone https://github.com/kanlishiyi/BoGuan.git
cd BoGuan
cp .env.example .env
# 编辑 .env 填入配置

# 2. 启动
docker compose up -d

# 访问 http://localhost:8081
```

### 方式三：pip 安装

```bash
pip install BoGuan

# 启动服务
boguan-platform
```

## ⚙ 配置说明

所有配置通过 `.env` 文件或环境变量设置：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ANTHROPIC_API_KEY` | LLM API 密钥 | *必填* |
| `ANTHROPIC_BASE_URL` | LLM API 地址 | `https://api.anthropic.com` |
| `ANTHROPIC_MODEL` | 模型名称 | `claude-sonnet-4-20250514` |
| `MCP_SERVER_URL` | MCP 服务器地址 | `http://localhost:10001/mcp` |
| `PLATFORM_PORT` | 服务端口 | `8081` |
| `DEFAULT_ADMIN_PASSWORD` | 默认管理员密码 | `admin123` |
| `TOOL_MAX_RETRIES` | 工具调用最大重试次数 | `3` |
| `TOOL_RETRY_DELAY` | 重试间隔（秒） | `2.0` |
| `PDF_WATERMARK_TEXT` | PDF 水印文字 | `boguan` |

## 📚 自定义 Skill

在 `skills/` 目录下创建新目录，并添加 `SKILL.md` 文件：

```markdown
---
name: my-custom-skill
description: 我的自定义技能描述
---

# 技能名称

技能的详细说明，包括：
- 能力范围
- 工作流程
- 输出格式

## 工作流程

1. 第一步：...
2. 第二步：...
```

保存后在 Agent 配置页面即可选择该技能。

## 🔌 MCP 工具接入

平台支持通过 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) 标准协议接入外部工具：

1. 在 Agent 配置页 → MCP 服务器区域添加你的 MCP 服务器地址
2. 点击"测试"验证连接，查看可用工具数量
3. 保存配置后，Agent 即可在对话中使用这些工具

## 🧪 示例脚本

```bash
# 环境快速验证
python examples/quick_test.py

# 列出 MCP 服务器所有工具
python examples/list_mcp_tools.py

# CLI 模式运行告警分析
python examples/alert_analysis_cli.py 488197
```

## 🛠 开发指南

### 本地开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check boguan/

# 启动开发服务（自动重载）
uvicorn boguan.app:app --reload --host 0.0.0.0 --port 8081
```

### API 文档

启动服务后访问自动生成的 API 文档：
- Swagger UI: http://localhost:8081/docs
- ReDoc: http://localhost:8081/redoc

### 核心模块说明

| 模块 | 说明 |
|------|------|
| `boguan.app` | FastAPI 应用入口，注册路由和启动事件 |
| `boguan.config` | 从 `.env` / 环境变量加载配置 |
| `boguan.core.runtime` | Agent 运行时生命周期管理，MemorySaver 多轮上下文 |
| `boguan.core.tools` | MCP 工具重试包装器 + 中文名称映射 |
| `boguan.core.skills` | 扫描 `skills/` 目录发现可用技能 |
| `boguan.core.pdf` | PDF 报告生成（中文字体 + 水印） |
| `boguan.api.auth` | Token 认证（登录/登出） |
| `boguan.api.agents` | Agent CRUD 接口 |
| `boguan.api.chat` | SSE 流式对话，集成 `astream_events` |
| `boguan.api.history` | 对话历史 JSON 持久化 |

## 🤝 贡献指南

欢迎贡献代码！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## ⭐ Star History

如果这个项目对你有帮助，请给一个 ⭐ Star！

## 📄 License

[Apache License 2.0](LICENSE) © 2024-2026 kanlishiyi
