#!/bin/bash

echo "🚀 启动 Manus Learn 系统"
echo "================================"

# 1. 停止现有容器
echo "📦 停止现有容器..."
cd /Users/yunpeng/Documents/github/manus-learn/007demo
docker-compose down 2>/dev/null || true

# 2. 启动 Docker 容器
echo "🐳 启动 Docker 容器..."
docker-compose up -d --build

# 3. 等待容器启动
echo "⏳ 等待容器启动..."
sleep 10

# 4. 检查容器状态
echo "📊 检查容器状态..."
docker ps | grep sandbox

# 5. 使用正确的 Python 运行任务
echo "🤖 运行任务..."
cd /Users/yunpeng/Documents/github/manus-learn/007demo

# 检查 Python 版本和 MCP 模块
echo "检查 Python 环境:"
python3.12 --version
python3.12 -c "import mcp; print('✅ MCP 模块可用')"

# 运行任务
python3.12 run_task.py "$@"