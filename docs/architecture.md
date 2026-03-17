# 系统架构

## 概述

博观 Agent 管理平台采用前后端分离的全栈架构，后端使用 FastAPI 提供 RESTful API 和 SSE 流式接口，前端为纯 HTML/CSS/JS 单页面应用。

## 架构图

```
                        ┌─────────────┐
                        │   浏览器     │
                        │  (用户界面)  │
                        └──────┬──────┘
                               │ HTTP / SSE
                        ┌──────┴──────┐
                        │   FastAPI    │
                        │   后端服务    │
                        └──────┬──────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
     ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
     │  DeepAgents  │   │   Skills    │   │     MCP     │
     │  Agent 引擎  │   │  知识库     │   │  工具协议    │
     └──────┬──────┘   └─────────────┘   └──────┬──────┘
            │                                    │
     ┌──────┴──────┐                     ┌──────┴──────┐
     │  LLM 模型   │                     │  外部工具    │
     │  (Anthropic) │                     │  & 数据源   │
     └─────────────┘                     └─────────────┘
```

## 模块说明

### 后端 (`boguan/`)

| 模块 | 职责 |
|------|------|
| `app.py` | FastAPI 应用入口，注册所有路由和启动事件 |
| `config.py` | 从 `.env` 文件和环境变量加载配置，提供全局 `settings` 单例 |
| `models.py` | Pydantic 数据模型定义（Agent、MCP、登录等请求体） |
| `api/auth.py` | 用户认证：登录登出、Token 管理 |
| `api/agents.py` | Agent CRUD：创建、读取、更新、删除 Agent |
| `api/chat.py` | 对话 SSE 流：将 LangGraph `astream_events` 转换为前端可消费的 SSE 事件 |
| `api/history.py` | 对话历史持久化：JSON 文件存储与加载 |
| `core/runtime.py` | Agent 运行时管理：构建 LLM、加载 MCP 工具、创建 DeepAgent 实例，缓存和多轮上下文 |
| `core/tools.py` | 工具重试包装器 + 中文名称映射 |
| `core/skills.py` | 扫描 `skills/` 目录，解析 SKILL.md 元数据 |
| `core/pdf.py` | PDF 报告生成：Markdown → 结构化 PDF，支持中文和水印 |

### 前端 (`static/`)

| 文件 | 说明 |
|------|------|
| `platform.html` | Agent 管理平台主页面，包含完整的 HTML/CSS/JS |
| `login.html` | 登录页面 |

### 技能知识库 (`skills/`)

每个技能是一个目录，包含 `SKILL.md` 文件：

```
skills/
├── alert-analysis/
│   └── SKILL.md          # 告警分析工作流程
├── monitoring-assistant/
│   └── SKILL.md          # 监控助手能力定义
└── pdf-report/
    └── SKILL.md          # PDF 报告格式模板
```

## 关键流程

### 对话流程

```
1. 用户发送消息
   ↓
2. 前端通过 SSE 连接 /api/agents/{aid}/chat?message=...
   ↓
3. 后端验证 Token，查找 Agent 配置
   ↓
4. 构建/复用 Agent 运行时（LLM + MCP 工具 + Skills）
   ↓
5. 调用 agent.astream_events() 流式执行
   ↓
6. 实时推送事件：
   - thinking: 思考过程
   - token: AI 回复文本
   - tool_call: 工具调用请求
   - tool_end: 工具返回结果
   - status: 状态更新
   - done: 完成
   ↓
7. 前端逐个渲染事件，展示完整的对话过程
```

### 多轮对话机制

- 使用 LangGraph 的 `MemorySaver` 作为 checkpointer
- 每个对话分配唯一 `thread_id`，checkpointer 自动维护上下文
- 服务重启后，通过持久化的历史消息恢复对话上下文
- 前端保存 `thread_id`，后续消息自动关联到同一对话线程

### 工具重试机制

```
工具调用 → 失败 → 重试 (1/3)
                → 重试 (2/3)
                → 重试 (3/3)
                → 全部失败 → 返回错误信息给 Agent
                           → Agent 跳过此工具，继续后续步骤
```

## 数据存储

| 数据 | 存储位置 | 格式 |
|------|----------|------|
| Agent 配置 | `data/agents.json` | JSON |
| 用户账号 | `data/users.json` | JSON |
| 对话历史 | `data/chat_history/{agent_id}.json` | JSON |
| 对话上下文 | 内存 (MemorySaver) | LangGraph State |
| Token 会话 | 内存 | Dict |
