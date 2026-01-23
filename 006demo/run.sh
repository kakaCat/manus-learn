#!/bin/bash
# 确保在项目根目录下运行
cd "$(dirname "$0")/.." || exit

# 检查虚拟环境（可选，根据您的环境调整）
# source venv/bin/activate

# 运行 Agent
# 如果有参数，直接传递给 Python 脚本
python 006demo/agent.py "$@"
