#!/bin/bash
# 确保在项目根目录下运行
cd "$(dirname "$0")" || exit

# 安装依赖
pip install -r requirements.txt

# 启动服务
# 注意：我们现在使用 main:app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
