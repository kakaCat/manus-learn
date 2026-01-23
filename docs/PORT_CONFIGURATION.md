# Manus Learn - 端口配置文档

## 📊 端口总览

| 服务 | 端口 | 协议 | 状态 | 用途 |
|------|------|------|------|------|
| **Frontend** | 5173 | HTTP | ✅ 运行中 | Vue 开发服务器 |
| **Backend** | 8000 | HTTP + WS | ✅ 运行中 | FastAPI + AI Agent |
| **Sandbox - noVNC** | 6080 | WebSocket | ✅ 运行中 | 浏览器远程桌面 |
| **Sandbox - VNC** | 5900 | VNC/RFB | ✅ 运行中 | 原生 VNC 客户端 |

---

## 🖥️ 前端 (Frontend)

### 基本信息
- **端口**: `5173`
- **访问地址**: http://localhost:5173
- **服务**: Vite 开发服务器
- **框架**: Vue 3 + Tailwind CSS

### 启动命令
```bash
cd frontend
npm run dev
```

### 环境变量 (可选)
```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/chat/ws
VITE_VNC_URL=ws://localhost:6080/websockify
```

### 前端调用的外部端口
- `localhost:8000` - Backend API (ChatPanel, SandboxMonitor)
- `localhost:6080` - noVNC WebSocket (AuxiliaryPanel)

---

## 🐍 后端 (Backend)

### 基本信息
- **端口**: `8000`
- **访问地址**: http://localhost:8000
- **服务**: FastAPI + Uvicorn
- **功能**: LangGraph Agent + MCP 工具集成

### 启动命令
```bash
cd backend
source venv/bin/activate  # 如果使用虚拟环境
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 配置文件
**backend/app/core/config.py**:
```python
backend_host: str = "0.0.0.0"
backend_port: int = 8000
cors_origins: list[str] = [
    "http://localhost:5173",  # 前端
    "http://localhost:3000",  # 备用
    "http://localhost:5174"   # 备用
]
```

**backend/.env**:
```bash
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### API 端点

#### 系统端点
- `GET /` - 服务信息
- `GET /health` - 健康检查
- `GET /docs` - Swagger 文档 (http://localhost:8000/docs)
- `GET /redoc` - ReDoc 文档

#### Chat API (`/api/chat`)
- `POST /api/chat` - REST 聊天接口
- `WebSocket /api/chat/ws` - WebSocket 实时聊天
- `POST /api/chat/clear` - 清除聊天历史
- `GET /api/chat/sessions` - 获取会话列表

#### Sandbox API (`/api/sandbox`)
- `GET /api/sandbox/status` - 沙盒状态
- `GET /api/sandbox/processes` - 进程列表
- `POST /api/sandbox/execute` - 执行命令 (如果有)

---

## 🐳 沙盒 (Sandbox)

### Docker Compose 端口映射

**sandbox/docker-compose.yml**:
```yaml
services:
  sandbox-os:
    ports:
      - "6080:6080"  # noVNC WebSocket 端口
      - "5900:5900"  # VNC 原生端口
    volumes:
      - ./shared:/root/shared
```

### VNC 端口 (5900)

- **协议**: VNC (RFB Protocol)
- **用途**: 原生 VNC 客户端连接
- **访问方式**:
  ```bash
  # macOS
  open vnc://localhost:5900

  # 使用 VNC Viewer
  # 地址: localhost:5900
  # 密码: (docker 配置中设置)
  ```

### noVNC 端口 (6080)

- **协议**: WebSocket (VNC over WebSocket)
- **用途**: 浏览器中查看沙盒桌面
- **访问方式**:
  - 通过前端: http://localhost:5173 (集成在 AuxiliaryPanel)
  - 直接访问: http://localhost:6080/vnc.html (如果 noVNC 提供)

**前端代码** (frontend/src/components/AuxiliaryPanel.vue):
```javascript
const VNC_URL = 'ws://localhost:6080/websockify'
```

---

## 🔗 端口连接拓扑

```
┌─────────────────────────────────────────────────────────┐
│                     用户浏览器                           │
│                 http://localhost:5173                   │
└──────────────┬────────────────┬─────────────────────────┘
               │                │
               │                │
      ┌────────▼────────┐  ┌───▼─────────────┐
      │  Backend API    │  │  noVNC WebSocket│
      │  localhost:8000 │  │  localhost:6080 │
      └────────┬────────┘  └───┬─────────────┘
               │                │
               │                │
      ┌────────▼────────────────▼─────────────┐
      │     Docker Sandbox Container          │
      │  ┌─────────────┐  ┌────────────────┐  │
      │  │ MCP Servers │  │  X11vnc + Xvfb │  │
      │  │ (stdio)     │  │  (VNC Server)  │  │
      │  └─────────────┘  └────────────────┘  │
      └───────────────────────────────────────┘
```

**数据流**:
1. 用户访问 http://localhost:5173 (前端)
2. 前端向 http://localhost:8000/api/chat 发送聊天请求
3. 后端调用 `docker exec` 与 MCP 服务器通信 (stdio)
4. 前端同时连接 ws://localhost:6080 显示沙盒桌面

---

## 🛠️ 端口管理命令

### 查看端口占用
```bash
# 查看所有项目端口
lsof -iTCP:5173,8000,6080,5900 -sTCP:LISTEN

# 查看特定端口
lsof -i :8000

# 使用 netstat (如果 lsof 不可用)
netstat -an | grep "LISTEN" | grep -E "5173|8000|6080|5900"
```

### 释放端口
```bash
# 方法1: 找到进程并杀死
lsof -ti :8000 | xargs kill -9

# 方法2: 停止服务
# Backend
pkill -f "uvicorn app.main"

# Frontend
pkill -f "vite"

# Sandbox
cd sandbox && docker-compose down
```

### 重启服务
```bash
# 方法1: 使用快速启动脚本
./scripts/quick_start.sh

# 方法2: 手动启动各服务
# Terminal 1 - Sandbox
cd sandbox && docker-compose up -d

# Terminal 2 - Backend
cd backend && python -m app.main

# Terminal 3 - Frontend
cd frontend && npm run dev
```

---

## 🔒 安全注意事项

### 1. 仅监听本地地址
- **生产环境**: 应该使用反向代理 (Nginx, Caddy)
- **开发环境**:
  - 前端 (Vite): 默认仅监听 localhost
  - 后端: 配置为 `0.0.0.0` 允许局域网访问 (可改为 `127.0.0.1`)

### 2. CORS 配置
后端已配置 CORS,仅允许以下来源:
```python
cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:5174"
]
```

### 3. 端口冲突
如果端口被占用,可以修改配置:

**前端** (frontend/vite.config.js):
```javascript
export default {
  server: {
    port: 5173,  // 改为其他端口,如 3000
  }
}
```

**后端** (backend/.env):
```bash
BACKEND_PORT=8000  # 改为其他端口,如 8080
```

**沙盒** (sandbox/docker-compose.yml):
```yaml
ports:
  - "6080:6080"  # 宿主机端口:容器端口
  - "5900:5900"
```

---

## 📝 快速参考

### 访问地址
- **前端**: http://localhost:5173
- **后端 API 文档**: http://localhost:8000/docs
- **后端健康检查**: http://localhost:8000/health
- **VNC 原生连接**: vnc://localhost:5900

### 常用测试命令
```bash
# 测试后端
curl http://localhost:8000/health

# 测试聊天 API
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"hello","chat_history":[]}'

# 测试前端
curl http://localhost:5173

# 测试 noVNC
curl http://localhost:6080
```

### 进程管理
```bash
# 查看运行中的服务
ps aux | grep -E "(vite|uvicorn|docker)" | grep -v grep

# 查看 Docker 容器
docker ps | grep sandbox
```

---

## 🐛 故障排除

### 问题: 端口已被占用

**症状**:
```
Error: listen EADDRINUSE: address already in use :::8000
```

**解决**:
```bash
# 1. 找到占用端口的进程
lsof -ti :8000

# 2. 杀死进程
lsof -ti :8000 | xargs kill -9

# 3. 或者修改配置使用其他端口
```

### 问题: 前端无法连接后端

**检查清单**:
1. ✅ 后端是否运行: `curl http://localhost:8000/health`
2. ✅ CORS 是否配置正确: 检查 `cors_origins`
3. ✅ 前端 API_URL 是否正确: 检查 `ChatPanel.vue`

### 问题: noVNC 无法显示

**检查清单**:
1. ✅ Sandbox 容器是否运行: `docker ps | grep sandbox`
2. ✅ VNC 服务是否启动: `docker exec sandbox-sandbox-os-1 ps aux | grep vnc`
3. ✅ 端口是否映射: `docker port sandbox-sandbox-os-1`

---

**最后更新**: 2026-01-22
**维护者**: Manus Learn Team
