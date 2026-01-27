#!/bin/bash

# 确保使用正确的 Python 版本
cd /Users/yunpeng/Documents/github/manus-learn/007demo

# 加载环境变量
source .env

# 使用 Python 3.12 运行脚本
python3.12 run_task.py "$@"