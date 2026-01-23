<template>
  <div class="auxiliary-panel glass-panel">
    <!-- Tabs Header -->
    <div class="panel-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['panel-tab', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
        :title="tab.name"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-name">{{ tab.name }}</span>
      </button>
    </div>

    <!-- Content Area -->
    <div class="panel-content">
      <!-- VNC View -->
      <div v-show="activeTab === 'vnc'" class="vnc-wrapper">
        <div class="vnc-controls">
          <div class="status-indicator">
            <span :class="['status-dot', vncStatusClass]"></span>
            {{ vncStatusText }}
          </div>
          <div class="vnc-actions">
            <button v-if="!isVNCConnected" @click="connectVNC" class="action-btn connect" title="Connect">
              ▶️ Connect
            </button>
            <button v-else @click="disconnectVNC" class="action-btn disconnect" title="Disconnect">
              ⏹️ Disconnect
            </button>
          </div>
        </div>
        <div ref="vncScreen" class="vnc-screen">
          <div v-if="!isVNCConnected" class="vnc-placeholder">
            <div class="placeholder-content">
              <span class="icon">🖥️</span>
              <p>Sandbox Desktop</p>
              <button @click="connectVNC" class="start-btn">Connect VNC</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Tools View -->
      <div v-if="activeTab === 'tools'" class="tools-wrapper">
        <div class="tools-header">
          <h3>🛠️ Sandbox Tools</h3>
          <p class="subtitle">Available tools for the AI agent</p>
        </div>
        <div class="tools-list">
           <div v-for="tool in toolsList" :key="tool.name" class="tool-item">
             <div class="tool-icon">{{ tool.icon }}</div>
             <div class="tool-info">
               <div class="tool-name">{{ tool.name }}</div>
               <div class="tool-desc">{{ tool.description }}</div>
             </div>
           </div>
        </div>
      </div>

      <!-- Monitor View -->
      <div v-if="activeTab === 'monitor'" class="monitor-wrapper">
        <SandboxMonitor />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import RFB from '@novnc/novnc/core/rfb'
import SandboxMonitor from './SandboxMonitor.vue'

// Props
const props = defineProps({
  initialTab: {
    type: String,
    default: 'vnc'
  }
})

// State
const activeTab = ref(props.initialTab || 'vnc')
const vncScreen = ref(null)
const rfb = ref(null)
const isVNCConnected = ref(false)
const vncStatusText = ref('Disconnected')
const vncStatusClass = ref('disconnected')

const VNC_URL = 'ws://localhost:6080/websockify'

const tabs = [
  { id: 'vnc', name: 'Desktop', icon: '🖥️' },
  { id: 'tools', name: 'Tools', icon: '🧰' },
  { id: 'monitor', name: 'System', icon: '📊' }
]

const toolsList = [
  { name: 'Shell', description: 'Execute shell commands in the sandbox', icon: '💻' },
  { name: 'File System', description: 'Read, write, and manage files', icon: '📁' },
  { name: 'Browser', description: 'Headless Chrome for web browsing', icon: '🌐' },
  { name: 'Python', description: 'Python 3.x execution environment', icon: '🐍' },
  { name: 'Node.js', description: 'Node.js runtime for JavaScript', icon: '📦' }
]

// VNC Functions
const connectVNC = () => {
  if (!vncScreen.value) {
    console.error('VNC screen element not found!')
    return
  }

  console.log('Container dimensions:', vncScreen.value.offsetWidth, 'x', vncScreen.value.offsetHeight)
  vncStatusText.value = 'Connecting...'
  vncStatusClass.value = 'connecting'

  try {
    rfb.value = new RFB(vncScreen.value, VNC_URL, {
      credentials: { password: '' }
    })

    rfb.value.addEventListener('connect', () => {
      isVNCConnected.value = true
      vncStatusText.value = 'Connected'
      vncStatusClass.value = 'connected'

      console.log('=== VNC CONNECTION DEBUG ===')
      console.log('Container:', vncScreen.value.offsetWidth, 'x', vncScreen.value.offsetHeight)
      console.log('Canvas:', rfb.value._canvas?.width, 'x', rfb.value._canvas?.height)
      console.log('Canvas offsetWidth:', rfb.value._canvas?.offsetWidth, 'x', rfb.value._canvas?.offsetHeight)
      console.log('Display size:', rfb.value._display?._viewportLoc)
      console.log('RFB scaleViewport:', rfb.value.scaleViewport)
      console.log('========================')

      // IMPORTANT: Set scaleViewport BEFORE calling any methods
      rfb.value.scaleViewport = true
      rfb.value.resizeSession = false

      // Force update viewport
      if (rfb.value._display && rfb.value._display.autoscale) {
        rfb.value._display.autoscale(vncScreen.value.offsetWidth, vncScreen.value.offsetHeight)
      }

      rfb.value.focus()

      // Log again after scaling
      setTimeout(() => {
        console.log('After scaling - Canvas:', rfb.value._canvas?.offsetWidth, 'x', rfb.value._canvas?.offsetHeight)
      }, 100)
    })

    rfb.value.addEventListener('disconnect', (detail) => {
      isVNCConnected.value = false
      vncStatusText.value = 'Disconnected'
      vncStatusClass.value = 'disconnected'
      if (detail && !detail.clean) {
        vncStatusText.value = 'Connection Lost'
        vncStatusClass.value = 'error'
      }
    })
    
    rfb.value.addEventListener('securityfailure', () => {
      vncStatusText.value = 'Security Failure'
      vncStatusClass.value = 'error'
    })

  } catch (error) {
    console.error('VNC connection error:', error)
    vncStatusText.value = 'Connection Error'
    vncStatusClass.value = 'error'
  }
}

const disconnectVNC = () => {
  if (rfb.value) {
    rfb.value.disconnect()
    rfb.value = null
  }
}

onMounted(() => {
  // Auto-connect if VNC tab is active
  if (activeTab.value === 'vnc') {
    setTimeout(connectVNC, 500)
  }
})

onUnmounted(() => {
  disconnectVNC()
})
</script>

<style scoped>
.auxiliary-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  color: #e0e0e0;
  overflow: hidden;
}

.panel-tabs {
  display: flex;
  padding: 0.5rem;
  background: rgba(37, 37, 37, 0.5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  gap: 0.5rem;
  flex-shrink: 0;
}

.panel-tab {
  flex: 1;
  padding: 0.6rem;
  border: none;
  background: transparent;
  color: #888;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.panel-tab:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #ccc;
}

.panel-tab.active {
  background: #333;
  color: #fff;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.panel-content {
  flex: 1;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

/* VNC Styles */
.vnc-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
}

.vnc-controls {
  padding: 0.5rem 1rem;
  background: #252525;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #333;
  height: 48px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #aaa;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
}

.status-dot.connected { background: #4caf50; box-shadow: 0 0 8px rgba(76, 175, 80, 0.4); }
.status-dot.connecting { background: #ff9800; }
.status-dot.error { background: #f44336; }
.status-dot.disconnected { background: #666; }

.action-btn {
  background: #333;
  border: 1px solid #444;
  color: #e0e0e0;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #444;
}

.action-btn.connect {
  color: #4caf50;
  border-color: rgba(76, 175, 80, 0.3);
}

.action-btn.disconnect {
  color: #f44336;
  border-color: rgba(244, 67, 54, 0.3);
}

.vnc-screen {
  flex: 1;
  background: #000;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  min-height: 0;
}

.vnc-screen :deep(canvas) {
  display: block;
  margin: auto;
}

.vnc-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  color: #666;
}

.placeholder-content {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.placeholder-content .icon {
  font-size: 3rem;
  opacity: 0.5;
}

.start-btn {
  background: #4caf50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.start-btn:hover {
  background: #43a047;
}

/* Tools Styles */
.tools-wrapper {
  padding: 1.5rem;
  overflow-y: auto;
  height: 100%;
}

.tools-header {
  margin-bottom: 1.5rem;
}

.tools-header h3 {
  margin: 0 0 0.5rem 0;
  color: #fff;
  font-size: 1.2rem;
}

.subtitle {
  margin: 0;
  color: #888;
  font-size: 0.9rem;
}

.tools-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tool-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: #2a2a2a;
  border-radius: 8px;
  border: 1px solid #333;
  transition: transform 0.2s;
}

.tool-item:hover {
  transform: translateY(-2px);
  border-color: #444;
}

.tool-icon {
  font-size: 1.5rem;
  background: #333;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-info {
  flex: 1;
}

.tool-name {
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 4px;
}

.tool-desc {
  font-size: 0.85rem;
  color: #aaa;
  line-height: 1.4;
}

/* Monitor Styles */
.monitor-wrapper {
  height: 100%;
  overflow: hidden; /* Let SandboxMonitor handle scroll */
}
</style>
