# ============================================================
# 博观 Agent 管理平台 - Docker 镜像
# ============================================================
# 构建: docker build -t boguan-agent .
# 运行: docker run -p 8081:8081 --env-file .env boguan-agent
# ============================================================

FROM python:3.12-slim AS base

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖（利用缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY boguan/ boguan/
COPY static/ static/
COPY skills/ skills/
COPY examples/ examples/
COPY pyproject.toml .
COPY LICENSE .
COPY README.md .

# 安装项目本身
RUN pip install --no-cache-dir -e .

# PDF 字体路径（使用 Linux 字体）
ENV PDF_FONT_DIR=/usr/share/fonts/truetype/wqy
ENV PDF_FONT_REGULAR=/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc
ENV PDF_FONT_BOLD=/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc

# 默认端口
EXPOSE 8081

# 数据目录（持久化挂载点）
VOLUME ["/app/data"]

# 启动命令
CMD ["python", "-m", "boguan.app"]
