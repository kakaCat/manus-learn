#!/bin/bash
# 快速启动 Manus AI Sandbox 的脚本

set -e

echo "🚀 Manus AI Sandbox 快速启动脚本"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查 Docker 是否运行
echo -n "检查 Docker... "
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}失败${NC}"
    echo "Docker 未运行。请先启动 Docker Desktop"
    exit 1
fi
echo -e "${GREEN}✓${NC}"

# 检查 Ollama 是否运行
echo -n "检查 Ollama... "
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}未运行${NC}"
    echo "正在启动 Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi
echo -e "${GREEN}✓${NC}"

# 启动 Docker 容器
echo -n "启动 Docker 容器... "
cd "${SCRIPT_DIR}/sandbox"
if docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}已在运行${NC}"
else
    docker-compose up -d > /dev/null 2>&1
    echo -e "${GREEN}✓${NC}"
fi

# 等待容器完全启动
echo -n "等待服务启动... "
sleep 10
echo -e "${GREEN}✓${NC}"

# 验证 MCP 服务
echo "验证 MCP 服务..."
docker exec sandbox-sandbox-os-1 bash -c "ps aux | grep -E '(mcp-shell|mcp-manager)' | grep -v grep" | while read line; do
    echo "  ${GREEN}✓${NC} $line"
done

cd "${SCRIPT_DIR}"

echo ""
echo "=================================="
echo -e "${GREEN}✅ Docker 容器启动成功！${NC}"
echo "=================================="
echo ""
echo "📋 下一步操作："
echo ""
echo "1. 启动后端（打开新终端）:"
echo "   cd ${SCRIPT_DIR}/backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "2. 启动前端（打开新终端）:"
echo "   cd ${SCRIPT_DIR}/sandbox/frontend"
echo "   npm run dev"
echo ""
echo "3. 访问监控面板:"
echo "   http://localhost:5173"
echo ""
echo "=================================="
echo ""
echo "💡 提示:"
echo "  - VNC 桌面: http://localhost:6080"
echo "  - 后端 API: http://localhost:8000"
echo "  - 查看容器日志: docker-compose -f ${SCRIPT_DIR}/sandbox/docker-compose.yml logs -f"
echo ""
