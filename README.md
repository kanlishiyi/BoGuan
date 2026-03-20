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

### 🎯 为什么选择 BoGuan

- **从“对话”升级到“可执行运维”**：不是只给答案，而是会调用工具、推进计划、输出结果沉淀
- **对管理者友好**：支持多 Agent 管理、权限登录、历史留存、配置热更新，方便团队协作
- **对一线运维友好**：执行计划与执行详情分区展示，能快速定位“现在做到哪一步、下一步做什么”
- **可落地、可扩展**：MCP + Skills 双扩展通道，适配企业已有监控平台和内部工具

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

### 🗂 执行计划可视化（推广亮点）
- **三段式工作台布局**：左侧 Agent、中间执行计划、右侧执行详情
- **计划状态实时变化**：支持待执行 / 进行中 / 已完成 / 已取消，且进行顺序自动校正
- **计划变更反馈**：新增/调整步骤高亮，便于识别动态重规划
- **执行链路清晰**：计划区只看“计划本身”，详情区专注“过程与证据”，信息不混杂

### 📊 PDF 报告生成
- 自动将分析结果转为结构化 PDF 文档
- 支持中文字体、自定义水印
- 包含告警概要、影响范围、排查过程、根因分析、处理建议等章节

### ✉️ 邮件报告分发
- 生成的根因报告可一键下载 PDF
- 支持将 PDF 报告发送到指定邮箱（SMTP）
- 对未配置 SMTP 的场景提供清晰错误提示，避免误判发送成功

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
| `SMTP_HOST` | SMTP 邮件服务器地址 | 空（不配置则禁用发邮件能力） |
| `SMTP_PORT` | SMTP 端口 | `587` |
| `SMTP_USER` | SMTP 登录用户名 | 空 |
| `SMTP_PASSWORD` | SMTP 登录密码 | 空 |
| `SMTP_FROM` | 发件人展示信息 | 空，默认使用 `SMTP_USER` |
| `SMTP_USE_TLS` | 是否使用 TLS | `true` |

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

## 📧 邮件 Skill 与 PDF 报告发送

BoGuan 内置了围绕“根因分析报告”的两类能力：

- `pdf-report`：将 AI 的分析结论整理为结构化 Markdown 报告，并自动生成 PDF 文件；
- `email-report`：在有了最终报告后，帮助用户通过邮件接收 PDF 报告。

### 1. 启用邮件发送（SMTP 配置）

在 `.env` 中补充（示例）：

```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alert-bot@example.com
SMTP_PASSWORD=your_password
SMTP_FROM=BoGuan Alert Bot <alert-bot@example.com>
SMTP_USE_TLS=true
```

> 如果不配置 `SMTP_HOST`，后端会直接报错提示，避免误以为邮件已发送。

### 2. 在 Agent 中勾选相关 Skills

1. 进入 Web 界面 → 左侧选择某个 Agent；
2. 在“📚 Skills 配置”中勾选：
   - `pdf-report`（PDF 分析报告生成）
   - `email-report`（告警报告邮件发送）
3. 保存配置。

### 3. 对话结束后的“导出与发送”操作

当某轮对话完成，Agent 输出了最终分析结论后，前端会在**最后一条 AI 消息下方**自动出现操作区（简体中文）：

- `📄 下载 PDF 报告`
- `✉️ 发送到邮箱`

两种方式都会：

1. 自动取当前轮对话中**最后一条 AI 文本**作为报告正文（通常是按 `pdf-report` 规范输出的结构化报告）；
2. 通过简短对话框引导用户输入：
   - 告警 ID（例如 `488197`），用于 PDF 标题与文件名；
   - 收件人邮箱（仅在“发送到邮箱”时需要）。

其中：

- “下载 PDF 报告” 会调用 `/api/agents/{aid}/report/pdf`，直接在浏览器中触发下载；
- “发送到邮箱” 会调用 `/api/agents/{aid}/report/email`，后端生成 PDF 并通过配置的 SMTP 服务器发送邮件，前端会用简体中文提示发送结果。

## 🧭 推理模式与任务计划视图

为了增强每轮问答的可解释性和可控性，博观平台在对话界面右侧提供了「任务计划」侧栏，并支持两种推理模式：

- **ReAct 模式**：边思考边行动，适合快速探索和排查；
- **Plan-and-Solver 模式**：先给出完整任务计划，再按计划逐步执行。

### 1. 在配置页选择推理模式

进入 Agent 配置页，在“🧭 推理模式”区域可以选择：

- `ReAct 模式`：Agent 会根据当前问题即时选择监控 / 日志等工具，计划栏会随着工具调用逐步填充和更新；
- `Plan-and-Solver 模式`：Agent 会先生成一份包含多步的任务计划（理解告警 → 收集证据 → 根因分析 → 输出报告），然后按计划逐步执行，并在每步下记录执行详情。

该配置会保存到 Agent 的 `llm_config.mode` 字段中，后续对话会根据该模式渲染右侧任务计划视图。

### 2. 每轮问答的任务计划与执行详情

在「💬 对话」页，每一轮用户发送消息后：

1. 中间「执行计划」栏会为当前轮次初始化一个任务列表：
   - ReAct：偏“即时信息收集 / 边查边推理”两大步骤；
   - Plan-and-Solver：细分为“理解告警 / 收集监控与日志数据 / 定位根因 / 输出报告与建议”等步骤。
2. 随着对话进行，任务计划会自动更新：
   - `thinking` 事件：抽取部分思考内容，简要展示为“思路：...”附加到当前进行中的步骤下；
   - `tool_call` / `tool_end` 事件：将工具调用与**参数摘要 / 结果摘要**挂在对应步骤下，并更新状态（进行中 / 已完成）；
   - DeepAgents `write_todos` 工具的输出会通过 `plan_update` 事件驱动右侧计划栏，真实反映计划的新增、调整和执行状态变化。
3. 当本轮对话完成（`done` 事件）时，计划中仍为“进行中”的步骤会被标记为“已完成”，让用户一目了然地看到本轮问答的推进路径。

为避免信息噪音，当前布局采用“三列分工”：

- 最左：智能体列表（选择与切换 Agent）
- 中间：执行计划状态变化（时间轴步骤 + 状态胶囊 + 变更高亮）
- 最右：执行详情（消息流、思考过程、工具调用、最终结论）

其中中间执行计划区只展示计划本身（步骤名称、状态、简短说明），不重复展示执行详情；执行细节统一在最右侧查看。

配合下方的「📄 下载 PDF 报告」与「✉️ 发送到邮箱」按钮，用户可以在同一个界面中，既看到对话细节，也看到任务级别的执行计划与结果沉淀。

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
