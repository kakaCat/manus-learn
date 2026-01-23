#!/bin/bash

# Manus AI Sandbox - Quick Start Script
# 快速启动整个 AI Sandbox 系统

set -e

echo "🚀 Manus AI Sandbox - Quick Start"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 步骤 1: 检查 Docker
echo -e "${YELLOW}📦 Step 1: Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is installed${NC}"
echo ""

# 步骤 2: 启动 Sandbox 容器
echo -e "${YELLOW}🐳 Step 2: Starting Sandbox Container...${NC}"
cd "$(dirname "$0")/../sandbox"
if docker-compose up -d; then
    echo -e "${GREEN}✅ Sandbox container started${NC}"
else
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
fi
echo ""

# 步骤 3: 等待 MCP 服务器启动
echo -e "${YELLOW}⏳ Step 3: Waiting for MCP servers to start (10s)...${NC}"
sleep 10

# 检查 MCP 服务状态
echo -e "${YELLOW}🔍 Checking MCP server status...${NC}"
docker exec sandbox-sandbox-os-1 supervisorctl status | grep mcp || true
echo ""

# 步骤 4: 检查 Ollama
echo -e "${YELLOW}🤖 Step 4: Checking Ollama...${NC}"
cd "$(dirname "$0")/.."
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama not found. Install with: brew install ollama${NC}"
    echo -e "${YELLOW}Then run: ollama serve${NC}"
    echo -e "${YELLOW}And pull a model: ollama pull qwen2.5:latest${NC}"
else
    echo -e "${GREEN}✅ Ollama is installed${NC}"
    
    # 检查 Ollama 是否运行
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama is running${NC}"
        
        # 列出可用模型
        echo -e "${YELLOW}Available models:${NC}"
        curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "No models found"
    else
        echo -e "${YELLOW}⚠️  Ollama is not running. Start with: ollama serve${NC}"
    fi
fi
echo ""

# 步骤 5: 设置后端环境
echo -e "${YELLOW}🔧 Step 5: Setting up Backend...${NC}"
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# 安装依赖
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env created. Please edit it if needed.${NC}"
fi

echo -e "${GREEN}✅ Backend environment ready${NC}"
echo ""

# 步骤 6: 提供启动选项
echo "=================================="
echo -e "${GREEN}✨ Setup Complete!${NC}"
echo "=================================="
echo ""
echo "Choose what to do next:"
echo ""
echo "1️⃣  Test AI Agent (automated tests):"
echo "   python test_agent.py --mode test"
echo ""
echo "2️⃣  Interactive Chat with AI:"
echo "   python test_agent.py --mode interactive"
echo ""
echo "3️⃣  Start Backend API Server:"
echo "   python main.py"
echo "   # or"
echo "   uvicorn main:app --reload"
echo ""
echo "4️⃣  Open Frontend (in browser):"
echo "   cd frontend"
echo "   npm run dev"
echo "   # Then open http://localhost:5173"
echo ""
echo "📚 Documentation:"
echo "   - MCP_MANAGER_FOR_AI.md - AI 使用指南"
echo "   - MCP_SYSTEM_ARCHITECTURE.md - 系统架构"
echo "   - backend/DEPLOYMENT.md - 后端部署"
echo ""

# 询问用户想要做什么
read -p "Do you want to run interactive chat now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 Starting interactive chat...${NC}"
    python test_agent.py --mode interactive
fi
