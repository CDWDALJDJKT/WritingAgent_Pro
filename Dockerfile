# 使用官方 Python 3.12 瘦身版镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 1. 复制依赖清单
COPY requirements.txt .

# 2. 安装依赖 (使用清华源加速，避免超时)
# --no-cache-dir 减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 复制项目所有代码
COPY . .

# 声明端口 (仅作文档说明)
EXPOSE 8000 8501