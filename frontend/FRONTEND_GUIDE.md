# 🎨 前端使用指南

## 概述

Manus AI Sandbox 前端是一个现代化的 Vue 3 应用，提供：
- 🖥️ VNC 远程桌面查看器
- 💬 AI Agent 聊天界面
- 📦 MCP 市场可视化管理

## 界面布局

```
┌──────────────────────────────────────────────────────┐
│  🤖 Manus AI Sandbox              VNC: Connected  ✅  │
├──────────────────┬──────────────────┬────────────────┤
│  🖥️ Sandbox      │  💬 AI Agent     │  📦 Marketplace│
│     Display       │      Chat        │     & Tools    │
│                   │                  │                │
│  [VNC Viewer]    │  [Chat Messages] │  [MCP Cards]   │
│                   │                  │                │
│  Connect  Disco   │  [Input Box]     │  [Install Btn] │
└──────────────────┴──────────────────┴────────────────┘
```

## 功能模块

### 1. VNC 远程桌面 (左侧)

**作用**: 实时查看 Docker 容器内的图形界面

**功能**:
- 查看浏览器自动化过程
- 监控命令执行效果
- 观察 xterm 终端操作

**使用**:
1. 点击 "Connect" 按钮
2. 等待连接建立（显示 "Connected"）
3. 可以看到容器内的桌面（Fluxbox + Xterm）

**技术**: 
- noVNC (WebSocket VNC 客户端)
- 连接到 `ws://localhost:6080`

### 2. AI Agent 聊天 (中间)

**作用**: 与 AI Assistant 对话，控制沙盒

**功能**:
- 💬 自然语言交互
- 🤖 AI 自主决策
- ⭐ AI 自己安装新工具

**示例对话**:

```
👤 You: What tools do you have?

🤖 AI: I have access to:
- MCP Manager for installing new capabilities
- Shell commands for running Linux commands
- File operations for reading/writing files
- Chrome browser automation

👤 You: I need you to search for "latest AI news"

🤖 AI: I don't have web search capability yet, but I can install it!
Let me check the marketplace...
[AI calls manager_list_available_mcps]
I found "Brave Search MCP"! Installing now...
[AI calls manager_install_mcp]
✅ Installed! Please restart container:
   cd sandbox && docker-compose restart
After restart, I'll be able to search for you!
```

**快捷键**:
- **Enter**: 发送消息
- **Shift + Enter**: 换行

**状态指示器**:
- 🟢 Connected - 后端连接正常
- 🔴 Disconnected - 后端未运行

### 3. MCP 市场 (右侧)

**作用**: 浏览和安装 MCP 工具

**功能**:
- 📋 查看可用 MCP 列表
- 🔍 按类别过滤
- 📥 一键安装
- ✅ 查看已安装状态

**MCP 类别**:
- 🌐 浏览器 (Browser) - Chrome, Puppeteer
- 🔍 搜索 (Search) - Brave Search
- 🛠️ 工具 (Tools) - Memory
- 📁 文件操作 (Files) - Filesystem

**安装流程**:
1. 在市场找到需要的 MCP
2. 点击 "📥 Install"
3. 等待安装完成
4. 按提示重启容器
5. 刷新页面，MCP 显示为 ✅ Installed

## 启动前端

### 开发模式

```bash
cd sandbox/frontend

# 首次运行 - 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:5173
```

### 生产构建

```bash
cd sandbox/frontend

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 前提条件

### 1. Docker 容器运行

```bash
cd sandbox
docker-compose up -d

# 验证 VNC 端口
curl http://localhost:6080
```

### 2. 后端 API 运行

```bash
cd backend
source venv/bin/activate
python main.py

# 或使用 uvicorn
uvicorn main:app --reload

# 验证后端
curl http://localhost:8000/health
```

### 3. Ollama 运行

```bash
ollama serve

# 验证 Ollama
ollama list
```

## API 集成

### 聊天 API

**端点**: `POST /api/chat`

**请求**:
```json
{
  "message": "What tools do you have?",
  "chat_history": []
}
```

**响应**:
```json
{
  "response": "I have access to shell commands, file operations, and browser automation...",
  "status": "success"
}
```

### 健康检查

**端点**: `GET /health`

```bash
curl http://localhost:8000/health
```

## 组件说明

### ChatPanel.vue

**位置**: `src/components/ChatPanel.vue`

**功能**:
- 消息列表显示
- 输入框和发送
- 加载状态
- 自动滚动

**Props**: 无

**Events**: 无（内部处理）

**API 调用**:
```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message, chat_history })
})
```

### MCPMarketplace.vue

**位置**: `src/components/MCPMarketplace.vue`

**功能**:
- MCP 列表展示
- 类别过滤
- 安装按钮
- 状态管理

**数据结构**:
```javascript
{
  id: 'brave-search',
  name: 'Brave Search MCP',
  description: '网络搜索能力',
  category: '搜索',
  official: true,
  installed: false,
  capabilities: ['web_search']
}
```

## 样式主题

### 颜色方案

```css
/* 背景 */
--bg-primary: #1e1e1e
--bg-secondary: #2d2d2d
--bg-tertiary: #3d3d3d

/* 文本 */
--text-primary: #e0e0e0
--text-secondary: #aaa
--text-muted: #888

/* 强调色 */
--accent-green: #4caf50
--accent-blue: #1976d2
--accent-orange: #ff9800
--accent-red: #f44336
```

### 响应式断点

```css
/* 桌面 (默认) */
grid-template-columns: 1fr 1fr 1fr;

/* 平板 (<1400px) */
grid-template-columns: 1fr 1fr;

/* 手机 (<900px) */
grid-template-columns: 1fr;
```

## 故障排除

### 1. VNC 无法连接

**问题**: 点击 Connect 后显示 "Connection Lost"

**解决**:
```bash
# 检查容器运行
docker ps | grep sandbox

# 检查 VNC 端口
docker exec sandbox-sandbox-os-1 ps aux | grep vnc

# 重启容器
docker-compose restart
```

### 2. 聊天无响应

**问题**: 发送消息后一直 loading

**解决**:
```bash
# 检查后端运行
curl http://localhost:8000/health

# 检查 Ollama
ollama list

# 查看后端日志
cd backend && python main.py
```

### 3. MCP 市场为空

**问题**: 市场显示 "Loading..." 或空白

**解决**:
1. 检查后端 API 连接
2. 查看浏览器控制台错误
3. 验证 CORS 设置（如果跨域）

### 4. 样式错乱

**问题**: 界面布局混乱

**解决**:
```bash
# 清除 node_modules 重新安装
rm -rf node_modules
npm install

# 清除构建缓存
rm -rf dist
npm run dev
```

## 开发技巧

### 1. 热重载

修改组件后自动刷新：
```bash
npm run dev
# 保存文件后浏览器自动更新
```

### 2. 调试

打开浏览器开发者工具：
- **Console**: 查看日志和错误
- **Network**: 检查 API 请求
- **Vue DevTools**: 检查组件状态

### 3. 添加新组件

```bash
# 创建新组件
touch src/components/NewComponent.vue

# 在 App.vue 中引入
import NewComponent from './components/NewComponent.vue'
```

## 性能优化

### 1. 消息虚拟化

如果聊天消息过多，考虑使用虚拟滚动：
```bash
npm install vue-virtual-scroller
```

### 2. 懒加载

对大型组件使用异步加载：
```javascript
const MCPMarketplace = defineAsyncComponent(() =>
  import('./components/MCPMarketplace.vue')
)
```

### 3. 图片优化

对 MCP 图标使用 SVG 或优化的 PNG。

## 未来功能

### 短期
- [ ] WebSocket 流式响应
- [ ] 消息搜索和过滤
- [ ] 聊天历史导出

### 中期
- [ ] MCP 工作流可视化
- [ ] 多会话管理
- [ ] 自定义主题

### 长期
- [ ] 移动端适配
- [ ] 离线支持 (PWA)
- [ ] 多语言支持

## 技术栈

- **框架**: Vue 3 + Composition API
- **构建工具**: Vite
- **VNC**: noVNC
- **HTTP 客户端**: Fetch API
- **样式**: Scoped CSS

## 文件结构

```
sandbox/frontend/
├── index.html                 # HTML 入口
├── package.json               # 依赖配置
├── vite.config.js             # Vite 配置
├── src/
│   ├── main.js                # Vue 应用入口
│   ├── App.vue                # 主应用组件
│   ├── style.css              # 全局样式
│   └── components/
│       ├── ChatPanel.vue      # 聊天面板
│       └── MCPMarketplace.vue # MCP 市场
└── FRONTEND_GUIDE.md          # 本文档
```

## 参考资料

- [Vue 3 文档](https://vuejs.org/)
- [noVNC GitHub](https://github.com/novnc/noVNC)
- [Vite 文档](https://vitejs.dev/)

---

**更新日期**: 2026-01-21
**版本**: 1.0.0
**作者**: Manus AI Sandbox Team
