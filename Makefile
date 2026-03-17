# ============================================================
# 博观 Agent 管理平台 - 开发命令
# ============================================================
# 使用方式: make <命令>
# Windows 用户: 需要安装 GNU Make 或使用 WSL
# ============================================================

.PHONY: help install dev run test lint fmt clean docker docker-up docker-down

# 默认目标
help: ## 显示帮助信息
	@echo.
	@echo   博观 Agent 管理平台 - 开发命令
	@echo   ================================
	@echo.
	@echo   make install    安装生产依赖
	@echo   make dev        安装开发依赖
	@echo   make run        启动服务
	@echo   make test       运行测试
	@echo   make lint       代码检查
	@echo   make fmt        代码格式化
	@echo   make clean      清理临时文件
	@echo   make docker     构建 Docker 镜像
	@echo   make docker-up  Docker Compose 启动
	@echo   make docker-down Docker Compose 停止
	@echo.

# ------ 安装 ------

install: ## 安装生产依赖
	pip install -r requirements.txt

dev: ## 安装开发依赖
	pip install -r requirements.txt
	pip install pytest pytest-asyncio ruff

# ------ 运行 ------

run: ## 启动平台服务
	python -m boguan.app

# ------ 测试 ------

test: ## 运行所有测试
	pytest tests/ -v --tb=short

test-cov: ## 运行测试并生成覆盖率报告
	pytest tests/ -v --tb=short --cov=boguan --cov-report=term-missing

# ------ 代码质量 ------

lint: ## Ruff 代码检查
	ruff check boguan/

fmt: ## Ruff 代码格式化
	ruff format boguan/
	ruff check boguan/ --fix

# ------ 清理 ------

clean: ## 清理临时文件和缓存
	@echo 清理 Python 缓存...
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .ruff_cache dist build *.egg-info 2>/dev/null || true
	@echo 清理完成.

# ------ Docker ------

docker: ## 构建 Docker 镜像
	docker build -t boguan-agent:latest .

docker-up: ## Docker Compose 启动
	docker compose up -d

docker-down: ## Docker Compose 停止
	docker compose down
