# 贡献指南

感谢你对 **BoGuan** 的关注！我们欢迎所有形式的贡献。

## 如何贡献

### 报告问题

- 在 [Issues](https://github.com/kanlishiyi/BoGuan/issues) 中搜索是否已有类似问题
- 如果没有，请创建新 Issue，包含：
  - 问题描述
  - 复现步骤
  - 期望行为 vs 实际行为
  - 环境信息（操作系统、Python 版本等）

### 提交代码

1. **Fork** 本仓库
2. **Clone** 到本地：`git clone https://github.com/your-username/BoGuan.git`
3. **创建分支**：`git checkout -b feature/your-feature`
4. **安装开发环境**：

```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
# .venv\Scripts\Activate.ps1  # Windows

pip install -e ".[dev]"
```

5. **编写代码和测试**
6. **运行检查**：

```bash
# 代码风格检查
ruff check boguan/

# 运行测试
pytest

# 本地启动验证
python -m boguan.app
```

7. **提交更改**：

```bash
git add .
git commit -m "feat: 你的功能描述"
```

8. **推送并创建 Pull Request**：

```bash
git push origin feature/your-feature
```

然后在 GitHub 上创建 Pull Request。

## Commit Message 规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

| 前缀 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加告警关联分析 Skill` |
| `fix` | 修复问题 | `fix: 修复 PDF 水印重叠问题` |
| `docs` | 文档更新 | `docs: 更新 MCP 接入指南` |
| `refactor` | 代码重构 | `refactor: 拆分 chat 模块` |
| `test` | 测试相关 | `test: 添加 Agent CRUD 单元测试` |
| `chore` | 构建/工具 | `chore: 更新依赖版本` |

## 项目结构

```
boguan/                 # 核心 Python 包
├── app.py              # FastAPI 入口
├── config.py           # 配置管理
├── models.py           # 数据模型
├── api/                # API 路由
│   ├── auth.py         # 认证
│   ├── agents.py       # Agent CRUD
│   ├── chat.py         # SSE 对话
│   └── history.py      # 对话历史
└── core/               # 核心逻辑
    ├── runtime.py      # Agent 运行时
    ├── tools.py        # 工具重试
    ├── skills.py       # Skill 发现
    └── pdf.py          # PDF 生成
```

## 添加新 Skill

在 `skills/` 目录下创建新目录，并添加 `SKILL.md`：

```markdown
---
name: my-skill
description: 技能描述
---

# 技能名称

详细说明...
```

## 代码风格

- 使用 [Ruff](https://github.com/astral-sh/ruff) 进行代码检查
- 行宽限制：100 字符
- 所有面向用户的文本使用简体中文
- 代码注释和 docstring 使用中文

## License

贡献的代码将遵循项目的 [Apache 2.0 License](LICENSE)。
