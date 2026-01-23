---
title: "Sandbox VNC：从零开始构建Docker沙盒环境"
description: "深度解析 Docker 沙盒环境的完整实现，从容器化到 VNC 远程桌面，从前端界面到系统编排，每一步都有可运行的代码和架构分析。"
image: "/images/blog/sandbox-vnc-overview.jpg"
keywords:
  - Docker
  - VNC
  - noVNC
  - Sandbox
  - Vue.js
  - Remote Desktop
  - Containerization
  - WebSocket
tags:
  - Sandbox
  - Docker
  - VNC
  - Vue.js
  - Implementation
  - Remote Access
author: "manus-learn"
date: "2026-01-20"
last_modified_at: "2026-01-20"
lang: "zh-CN"
audience: "开发者 / DevOps工程师 / 对容器化和远程桌面感兴趣的开发者"
difficulty: "intermediate"
estimated_read_time: "15-20min"
topics:
  - Sandbox Development
  - Docker Implementation
  - VNC Integration
  - Vue.js Frontend
  - Container Orchestration
---

# 从零开始构建 Manus 系统： 01-Sandbox VNC

## 📍 导航指南

Manus中重要的组成部分就是沙盒的实现。根据你的背景，选择合适的阅读路径：

- 🎓 **入门者？** → [第一部分：基础环境搭建](#part-1) - 了解 Docker 容器和 X11 显示的基本原理
- 🛠️ **实践者？** → [第二部分：VNC服务实现](#part-2) - 学习 VNC 协议和 WebSocket 代理
- 🎨 **前端开发者？** → [第三部分：现代化界面](#part-3) - 掌握 Vue.js + noVNC 的集成开发
- 🏗️ **架构师？** → [第四部分：代码实现](#part-4) - 理解完整的代码与实现

---

## 目录

### 第一部分：基础环境搭建 🌱
- [第一阶段：Docker容器环境](#stage-1)
  - [Ubuntu基础镜像与X11环境](#ubuntu-x11)
  - [Supervisor进程管理](#supervisor)
- [第二阶段：虚拟桌面实现](#stage-2)
  - [Xvfb无头显示](#xvfb)
  - [Fluxbox窗口管理器](#fluxbox)

### 第二部分：VNC服务实现 📡
- [第三阶段：VNC服务器配置](#stage-3)
  - [x11vnc高性能服务器](#x11vnc)
  - [websockify WebSocket代理](#websockify)
- [第四阶段：网络通信层](#stage-4)
  - [端口映射与安全](#port-mapping)
  - [连接协议优化](#protocol-optimization)

### 第三部分：现代化界面 🎨
- [第五阶段：Vue.js前端开发](#stage-5)
  - [noVNC客户端集成](#novnc-integration)
  - [实时状态管理](#state-management)
- [第六阶段：用户体验优化](#stage-6)
  - [响应式设计](#responsive-design)
  - [错误处理机制](#error-handling)

### 第四部分：代码实现 🚀
- [第七阶段：沙盒实现](#stage-7)
  - [Dockerfile](#dockerfile)
  - [supervisord.conf](#supervisord-conf)
  - [docker-compose配置](#docker-compose)
  - [前端代码](#frontend-code)

### 附录
- [常见问题 FAQ](#faq)

---

## 引言

随着 Agentic AI（代理式人工智能）的兴起，AI 自主操作计算机工具的能力成为了关键。然而，直接在用户主机上运行这些操作面临着安全风险和交互冲突的挑战。作为当前领先的高级 Agent 实现，Manus 通过将 AI 操作限制在安全的沙盒环境中完美解决了这一问题。

沙盒实现方案的核心价值在于：
1. **安全隔离**：通过容器化技术确保 AI 操作与宿主机完全隔离，保障数据与系统安全。
2. **无感交互**：独立桌面环境防止了 AI 与人类用户争夺鼠标键盘控制权，实现并行工作。
3. **实时观测**：基于 WebSocket 的 VNC 传输，让用户能实时“监工” AI 的操作过程。
4. **现代体验**：结合 Vue.js 与 noVNC，提供流畅、无插件的 Web 桌面访问体验。
5. **一键部署**：标准化的 docker-compose 编排，让复杂环境的搭建变得简单高效。

---

<a id="part-1"></a>
## 第一部分：基础环境搭建 🌱

<a id="stage-1"></a>
### 第一阶段：Docker容器环境

> **背景**：容器化是沙盒环境的基础，它提供了进程隔离和资源限制，让沙盒内的操作不会影响主机系统。

<a id="ubuntu-x11"></a>
#### Ubuntu基础镜像与X11环境

这一阶段的核心是构建一个支持图形界面的 Ubuntu 容器环境。

**核心逻辑**：
- 选择 Ubuntu 22.04 LTS 作为基础镜像，确保长期支持
- 安装 X11 虚拟显示相关的核心组件
- 配置无交互式安装以适应自动化构建

**Dockerfile 核心配置**：

```dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    supervisor \
    novnc \
    websockify \
    # ... 其他工具
```

**关键技术点**：
- `DEBIAN_FRONTEND=noninteractive`：避免安装过程中的交互式提示
- 镜像大小优化：使用阿里云镜像源加速下载

<a id="supervisor"></a>
#### Supervisor进程管理

在容器环境中，Supervisor 扮演着"进程守护者"的角色，确保所有服务稳定运行。

**配置示例**：

```ini
[supervisord]
nodaemon=true

[program:xvfb]
command=/usr/bin/Xvfb :1 -screen 0 1280x800x24
autorestart=true

[program:fluxbox]
command=/usr/bin/fluxbox
environment=DISPLAY=":1"
autorestart=true
```

**优势**：
- 自动重启崩溃的服务
- 统一日志管理
- 进程依赖控制

---

<a id="stage-2"></a>
### 第二阶段：虚拟桌面实现

<a id="xvfb"></a>
#### Xvfb无头显示

Xvfb (X Virtual Framebuffer) 是实现无头桌面的核心组件。

**工作原理**：
- 创建虚拟的 X11 显示服务器 (:1)
- 不需要物理显示设备
- 支持标准 X11 协议

<a id="fluxbox"></a>
#### Fluxbox窗口管理器

作为轻量级窗口管理器，Fluxbox 提供了基本的桌面环境。

**特点**：
- 资源占用极低 (< 10MB 内存)
- 响应速度快
- 支持基本的窗口操作

---

<a id="part-2"></a>
## 第二部分：VNC服务实现 📡

<a id="stage-3"></a>
### 第三阶段：VNC服务器配置

<a id="x11vnc"></a>
#### x11vnc高性能服务器

x11vnc 将 X11 显示转换为 VNC 协议。

**核心配置**：
```ini
[program:x11vnc]
command=/usr/bin/x11vnc -display :1 -nopw -listen localhost -xkb -ncache 10 -ncache_cr -forever
autorestart=true
```

**性能优化**：
- `-ncache 10`：启用客户端缓存，减少带宽
- `-ncache_cr`：压缩重复区域
- `-forever`：持续运行

<a id="websockify"></a>
#### websockify WebSocket代理

websockify 实现 TCP 到 WebSocket 的协议转换。

**命令配置**：
```ini
[program:websockify]
command=/usr/bin/websockify --web=/usr/share/novnc/ 6080 localhost:5900
autorestart=true
```

**技术价值**：
- 支持浏览器原生 WebSocket
- 无需 Flash 或 Java 插件
- 提供 noVNC Web 界面

---

<a id="stage-4"></a>
### 第四阶段：网络通信层

<a id="port-mapping"></a>
#### 端口映射与安全

Docker Compose 配置了安全的端口映射：

```yaml
services:
  sandbox-os:
    ports:
      - "6080:6080"  # WebSocket/VNC Web
      - "5900:5900"  # VNC TCP (可选)
```

<a id="protocol-optimization"></a>
#### 连接协议优化

**WebSocket 优势**：
- 全双工通信
- 低延迟 (< 50ms)
- 防火墙友好

---

<a id="part-3"></a>
## 第三部分：现代化界面 🎨

<a id="stage-5"></a>
### 第五阶段：Vue.js前端开发

<a id="novnc-integration"></a>
#### noVNC客户端集成

Vue.js 与 noVNC 的无缝集成：

```javascript
import RFB from '@novnc/novnc/core/rfb'

const connect = () => {
  rfb.value = new RFB(screen.value, 'ws://localhost:6080/websockify')
  // 事件处理
}
```

<a id="state-management"></a>
#### 实时状态管理

响应式状态跟踪连接状态：

```javascript
const isConnected = ref(false)
const statusText = ref('Disconnected')
```

---

<a id="stage-6"></a>
### 第六阶段：用户体验优化

<a id="responsive-design"></a>
#### 响应式设计

CSS 实现自适应布局：

```css
.screen-container {
  flex: 1;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
}
```

<a id="error-handling"></a>
#### 错误处理机制

完善的连接状态反馈和错误处理。

---

<a id="part-4"></a>
## 第四部分：系统集成与部署 🚀

<a id="stage-7"></a>
### 第七阶段：沙盒实现

<a id="dockerfile"></a> 
#### Dockerfile
```dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN sed -i 's/ports.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    supervisor \
    novnc \
    websockify \
    net-tools \
    python3-numpy \
    xterm \
    && rm -rf /var/lib/apt/lists/*

# Configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Environment variables
ENV DISPLAY=:1
ENV RESOLUTION=1280x800

# Expose ports
# 5900: VNC (TCP)
# 6080: noVNC (HTTP/WebSocket)
EXPOSE 5900 6080

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

```

<a id="supervisord-conf"></a>
#### supervisord.conf

**核心配置**：
```ini
; Global supervisord configuration
[supervisord]
nodaemon=true
logfile=/var/log/supervisord.log
pidfile=/var/run/supervisord.pid

; Xvfb - Virtual framebuffer X server for headless display
[program:xvfb]
command=/usr/bin/Xvfb :1 -screen 0 1280x800x24
autorestart=true
priority=100

; Fluxbox - Lightweight window manager for the virtual display
[program:fluxbox]
command=/usr/bin/fluxbox
environment=DISPLAY=":1"
autorestart=true
priority=200

; Xterm - Terminal emulator running on the virtual display
[program:xterm]
command=/usr/bin/xterm -geometry 80x24+10+10 -ls -title "Sandbox Terminal"
environment=DISPLAY=":1"
autorestart=true
priority=300

; x11vnc - VNC server that shares the virtual X display
[program:x11vnc]
command=/usr/bin/x11vnc -display :1 -nopw -listen localhost -xkb -ncache 10 -ncache_cr -forever
autorestart=true
priority=400

; Websockify - WebSocket to TCP proxy for noVNC web client
[program:websockify]
command=/usr/bin/websockify --web=/usr/share/novnc/ 6080 localhost:5900
autorestart=true
priority=500

```

<a id="docker-compose"></a>
#### docker-compose配置

一键部署配置：

```yaml
services:
  sandbox-os:
    build: ./docker
    ports:
      - "6080:6080"
      - "5900:5900"
    volumes:
      - ./shared:/root/shared
```
容器执行：
```bash
docker-compose up -d --build
```

<a id="frontend-code"></a>
#### 前端代码

```javascript
<template>
  <div class="container">
    <header>
      <h1>Sandbox VNC Viewer</h1>
      <div class="status" :class="statusClass">{{ statusText }}</div>
      <div class="controls">
        <button @click="connect" :disabled="isConnected">Connect</button>
        <button @click="disconnect" :disabled="!isConnected">Disconnect</button>
      </div>
    </header>
    <div ref="screen" class="screen-container">
      <!-- Canvas will be injected here by RFB -->
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import RFB from '@novnc/novnc/core/rfb'

const screen = ref(null)
const rfb = ref(null)
const isConnected = ref(false)
const statusText = ref('Disconnected')
const statusClass = ref('disconnected')

const VNC_URL = 'ws://localhost:6080/websockify'

const connect = () => {
  if (!screen.value) return

  statusText.value = 'Connecting...'
  statusClass.value = 'connecting'

  try {
    rfb.value = new RFB(screen.value, VNC_URL)

    rfb.value.addEventListener('connect', () => {
      isConnected.value = true
      statusText.value = 'Connected'
      statusClass.value = 'connected'
      rfb.value.focus()
    })

    rfb.value.addEventListener('disconnect', (detail) => {
      isConnected.value = false
      statusText.value = 'Disconnected'
      statusClass.value = 'disconnected'
      if (detail.clean) {
        console.log('Clean disconnect')
      } else {
        console.error('Unexpected disconnect', detail)
        statusText.value = 'Connection Lost'
        statusClass.value = 'error'
      }
    })

    rfb.value.addEventListener('credentialsrequired', () => {
        // Handle password if needed
        // rfb.value.sendCredentials({ password: 'your-password' });
    })

  } catch (error) {
    console.error('Connection error:', error)
    statusText.value = 'Error'
    statusClass.value = 'error'
  }
}

const disconnect = () => {
  if (rfb.value) {
    rfb.value.disconnect()
  }
}

onMounted(() => {
  // Auto connect optional
  // connect()
})

onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

header {
  padding: 1rem;
  background: #1a1a1a;
  color: white;
  display: flex;
  align-items: center;
  gap: 20px;
}

h1 {
  margin: 0;
  font-size: 1.2rem;
}

.screen-container {
  flex: 1;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.screen-container :deep(canvas) {
  box-shadow: 0 0 20px rgba(0,0,0,0.5);
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.status.connected { background: #4caf50; }
.status.disconnected { background: #9e9e9e; }
.status.connecting { background: #ff9800; }
.status.error { background: #f44336; }

button {
  padding: 6px 12px;
  cursor: pointer;
  background: #333;
  color: white;
  border: 1px solid #555;
  border-radius: 4px;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

![sandbox.png](https://p0-xtjj-private.juejin.cn/tos-cn-i-73owjymdk6/ee46f8baa698480fae142943b3f66a9f~tplv-73owjymdk6-jj-mark-v1:0:0:0:0:5o6Y6YeR5oqA5pyv56S-5Yy6IEAg5Lik5LiH5LqU5Y2D5Liq5bCP5pe2:q75.awebp?policy=eyJ2bSI6MywidWlkIjoiMzk2NjY5MzY4Mjk3MTg3MCJ9&rk3s=e9ecf3d6&x-orig-authkey=f32326d3454f2ac7e96d3d06cdbb035152127018&x-orig-expires=1768986325&x-orig-sign=NoYf9VbZo97SCVEbPqoOXFvKp3w%3D)
---

<a id="faq"></a>
## 常见问题 FAQ

**Q: 为什么选择 noVNC 而不是其他解决方案？**
A: noVNC 是纯 JavaScript 实现，无需插件，在现代浏览器中表现优秀，且开源社区活跃。

**Q: 如何处理高分辨率显示？**
A: 可以调整 Xvfb 参数，如 `1280x800x24`，支持更高分辨率，但需要考虑带宽和性能。

**Q: 安全性如何保证？**
A: 默认配置为本地访问，如需公网部署，建议添加 VNC 密码、SSL 加密和防火墙规则。

---


## 📝 结语

至此，我们已经成功构建了一个安全、可视化的 Docker 沙盒环境。通过 Xvfb、x11vnc 和 noVNC 的组合，我们不仅实现了系统的隔离，还为用户提供了一个直观的观察窗口。

这就像是为未来的 AI 助手建造了一间功能完备的“工作室”。目前，这个工作室虽然安全且可视，但还需要赋予 AI 远程操控这里一切的“双手”。

在接下来的文章中，我们将开始构建 AI Agent 的核心能力。首先，我们将实现 **Shell Agent**，赋予 AI 在这个沙盒中执行系统命令的能力，让它真正“动”起来。敬请期待！