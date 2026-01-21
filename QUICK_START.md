# 🚀 快速启动 Manus AI Sandbox

## 当前状态

✅ Docker 容器正在运行
✅ MCP 服务器部分运行中：
  - ✅ mcp-shell (命令执行)
  - ✅ mcp-filesystem (文件操作)
  - ✅ mcp-manager (MCP 管理)
  - ⚠️ mcp-chrome (暂时离线，不影响核心功能)

## 立即开始

### 1. 启动后端服务（新终端）

```bash
cd /Users/yunpeng/Documents/github/manus-learn/backend

# 如果还没有虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖（首次运行）
pip install -r requirements.txt

# 启动后端
python main.py
```

预期输出：
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. 启动前端服务（新终端）

```bash
cd /Users/yunpeng/Documents/github/manus-learn/sandbox/frontend

# 安装依赖（首次运行）
npm install

# 启动前端
npm run dev
```

预期输出：
```
VITE v5.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

### 3. 访问监控面板

打开浏览器访问：**http://localhost:5173**

## 功能演示

### 📊 左侧面板 - 监控仪表板（默认）

实时监控包括：
- **状态卡片**: 容器状态、MCP 数量（3个运行中）、进程总数
- **资源使用**: CPU、内存、磁盘使用率（带彩色进度条）
- **MCP 服务器**:
  - 🟢 mcp-shell (RUNNING)
  - 🟢 mcp-filesystem (RUNNING)
  - 🟢 mcp-manager (RUNNING)
  - 🔴 mcp-chrome (FATAL - 暂时离线)
- **运行进程**: Top 10 进程（按 CPU 排序）
- **实时日志**: 最近 50 行 supervisord 日志

**自动刷新**: 每 5 秒更新一次

切换到 VNC 标签可查看远程桌面。

### 💬 中间面板 - AI 聊天

与 AI Agent 交互示例：

```
你: Hello! 列出当前可用的 MCP 工具
AI: [调用 manager_list_installed_mcps]
    当前安装了 3 个 MCP 工具：
    - filesystem: 文件操作
    - shell: 命令执行
    - manager: MCP 管理

你: 列出 /root/shared/workspace 目录的文件
AI: [调用 filesystem_list_directory]
    目录内容: ...

你: 创建一个文件 test.txt，内容是 "Hello Manus!"
AI: [调用 filesystem_write_file]
    ✅ 文件创建成功！

你: 执行命令 ls -la
AI: [调用 shell_execute_command]
    输出: total 8
          drwxr-xr-x ...
```

**注意**: 确保后端已启动，连接状态显示为 "Connected"（绿色）。

### 📦 右侧面板 - MCP 市场

- 浏览可用的 MCP 工具
- 查看已安装的工具
- 一键安装新工具（如 Memory MCP、Brave Search）

## 故障排除

### 问题 1: 前端显示 "Disconnected"

**原因**: 后端未启动或无法连接

**解决**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 如果没有响应，启动后端
cd backend
source venv/bin/activate
python main.py
```

### 问题 2: 聊天输入框禁用

**原因**: 同上，后端未连接

**检查**: 查看聊天面板顶部状态，应该显示 "Connected"（绿色）

### 问题 3: 监控面板显示 "Loading..."

**原因**:
1. 后端未运行
2. Docker 容器未运行
3. MCP 服务未启动

**解决**:
```bash
# 1. 检查容器
docker ps | grep sandbox
# 应该显示 Up 状态

# 2. 检查 MCP 服务
docker logs sandbox-sandbox-os-1 | grep "RUNNING"

# 3. 如果容器未运行
cd /Users/yunpeng/Documents/github/manus-learn/sandbox
docker-compose up -d

# 4. 如果容器运行但 MCP 未运行
docker-compose restart
```

### 问题 4: MCP Chrome 显示 FATAL

**状态**: 已知问题，Chrome MCP 路径需要修复

**影响**: 不影响核心功能（文件、命令、MCP 管理都正常）

**临时解决**: 暂时不使用浏览器自动化功能

**永久修复**（可选）:
```bash
# 已修改配置文件，需要重新构建镜像
cd /Users/yunpeng/Documents/github/manus-learn/sandbox
docker-compose down
docker-compose build
docker-compose up -d
```

### 问题 5: AI 响应很慢

**原因**: Ollama 模型加载或推理慢

**优化**:
1. 使用更小的模型：
   ```bash
   ollama pull qwen2.5:0.5b  # 超小模型
   ```

2. 修改后端配置（backend/config.py）:
   ```python
   ollama_model: str = Field(default="qwen2.5:0.5b")
   ```

## 测试功能清单

### ✅ 监控面板
- [ ] 打开 http://localhost:5173
- [ ] 查看状态卡片（Container: Running, MCP Servers: 3）
- [ ] 查看资源使用率（CPU、内存、磁盘条形图）
- [ ] 查看 MCP 服务器列表（3 个绿点）
- [ ] 查看进程列表（应该有 10+ 进程）
- [ ] 查看日志滚动
- [ ] 等待 5 秒，确认数据自动刷新

### ✅ AI 聊天
- [ ] 检查顶部状态为 "Connected"（绿色）
- [ ] 输入 "Hello"，点击 Send
- [ ] 观察 AI 响应
- [ ] 测试命令：列出已安装的 MCP
- [ ] 测试命令：列出目录文件
- [ ] 测试命令：创建文本文件

### ✅ VNC 查看器
- [ ] 点击左侧面板的 "🖥️ VNC" 标签
- [ ] 点击 "Connect" 按钮
- [ ] 观察状态变为 "Connected"（绿色）
- [ ] 查看沙盒桌面（Fluxbox + Xterm）
- [ ] 点击 "Disconnect" 断开连接

### ✅ MCP 市场
- [ ] 点击右侧面板的 "📦 Marketplace" 标签
- [ ] 查看可用的 MCP 工具列表
- [ ] 点击一个工具查看详情

## 高级功能

### 安装新的 MCP 工具

**通过 AI Agent**:
```
你: 帮我安装 Memory MCP 工具
AI: [调用 manager_list_available_mcps 查找]
    [调用 manager_install_mcp 安装]
    安装成功！请重启容器：docker-compose restart
```

**通过市场 UI**:
1. 点击右侧 Marketplace 标签
2. 找到 Memory MCP
3. 点击 "Install" 按钮
4. 等待安装完成
5. 重启容器：
   ```bash
   cd /Users/yunpeng/Documents/github/manus-learn/sandbox
   docker-compose restart
   ```

### 让 AI 使用新工具

安装并重启后：
```
你: 存储一条记忆：我的名字是 Tom
AI: [使用 memory_store 工具]
    ✅ 记忆已保存

你: 我的名字是什么？
AI: [使用 memory_recall 工具]
    你的名字是 Tom
```

## 完整架构图

```
浏览器 (http://localhost:5173)
  ├── 左侧: 监控面板/VNC
  ├── 中间: AI 聊天
  └── 右侧: MCP 市场
       ↓ HTTP/WS
后端 (http://localhost:8000)
  ├── FastAPI REST API
  ├── LangChain Agent
  └── Ollama LLM (qwen2.5)
       ↓ MCP Protocol (stdio)
Docker 容器 (sandbox-sandbox-os-1)
  ├── VNC 服务 (port 6080)
  ├── mcp-shell (命令执行)
  ├── mcp-filesystem (文件操作)
  ├── mcp-manager (MCP 管理)
  └── mcp-chrome (浏览器 - 暂时离线)
```

## 下一步

现在系统已经可以使用了！你可以：

1. **熟悉监控面板**: 观察沙盒实时状态
2. **与 AI 交互**: 尝试各种命令和任务
3. **安装新工具**: 从市场安装 Memory、Brave Search 等
4. **查看 VNC**: 实时观察命令执行效果
5. **修复 Chrome MCP**（可选）: 重新构建镜像

## 停止服务

```bash
# 停止前端（Ctrl+C 在前端终端）
# 停止后端（Ctrl+C 在后端终端）

# 停止 Docker 容器
cd /Users/yunpeng/Documents/github/manus-learn/sandbox
docker-compose down
```

## 重启全部服务

```bash
# 1. 启动 Docker
cd /Users/yunpeng/Documents/github/manus-learn/sandbox
docker-compose up -d

# 2. 启动后端（新终端）
cd ../backend
source venv/bin/activate
python main.py

# 3. 启动前端（新终端）
cd ../sandbox/frontend
npm run dev

# 4. 打开浏览器
open http://localhost:5173
```

---

**祝你使用愉快！🎉**

如有问题，请检查上面的故障排除部分。
