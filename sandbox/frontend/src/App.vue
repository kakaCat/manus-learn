<template>
  <div class="app-container">
    <!-- Top Header -->
    <header class="app-header">
      <h1>🤖 Manus AI Sandbox</h1>
      <div class="header-controls">
        <div class="vnc-status" :class="vncStatusClass">
          VNC: {{ vncStatusText }}
        </div>
        <button @click="connectVNC" :disabled="isVNCConnected" class="connect-btn">
          Connect VNC
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Left Panel: Monitoring/VNC Tabs -->
      <div class="left-panel">
        <div class="panel-header">
          <div class="left-tabs">
            <button
              :class="['left-tab', { active: leftPanelTab === 'monitor' }]"
              @click="leftPanelTab = 'monitor'"
            >
              📊 Monitor
            </button>
            <button
              :class="['left-tab', { active: leftPanelTab === 'vnc' }]"
              @click="leftPanelTab = 'vnc'"
            >
              🖥️ VNC
            </button>
          </div>
          <div v-if="leftPanelTab === 'vnc'" class="vnc-controls">
            <button @click="connectVNC" :disabled="isVNCConnected" class="small-btn">
              Connect
            </button>
            <button @click="disconnectVNC" :disabled="!isVNCConnected" class="small-btn">
              Disconnect
            </button>
          </div>
        </div>

        <!-- Monitor View -->
        <div v-if="leftPanelTab === 'monitor'" class="monitor-wrapper">
          <SandboxMonitor />
        </div>

        <!-- VNC View -->
        <div v-else ref="vncScreen" class="vnc-container">
          <!-- Canvas injected by RFB -->
        </div>
      </div>

      <!-- Middle Panel: AI Chat -->
      <div class="middle-panel">
        <ChatPanel />
      </div>

      <!-- Right Panel: MCP Marketplace -->
      <div class="right-panel">
        <div class="tab-container">
          <div class="tabs">
            <button 
              :class="['tab', { active: activeTab === 'marketplace' }]"
              @click="activeTab = 'marketplace'"
            >
              📦 Marketplace
            </button>
            <button 
              :class="['tab', { active: activeTab === 'tools' }]"
              @click="activeTab = 'tools'"
            >
              🛠️ Tools
            </button>
          </div>
          
          <div class="tab-content">
            <MCPMarketplace v-if="activeTab === 'marketplace'" />
            <div v-else class="tools-panel">
              <h3>🛠️ Installed Tools</h3>
              <p>Coming soon...</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import RFB from '@novnc/novnc/core/rfb'
import ChatPanel from './components/ChatPanel.vue'
import MCPMarketplace from './components/MCPMarketplace.vue'
import SandboxMonitor from './components/SandboxMonitor.vue'

const vncScreen = ref(null)
const rfb = ref(null)
const isVNCConnected = ref(false)
const vncStatusText = ref('Disconnected')
const vncStatusClass = ref('disconnected')
const activeTab = ref('marketplace')
const leftPanelTab = ref('monitor') // 'monitor' or 'vnc'

const VNC_URL = 'ws://localhost:6080/websockify'

const connectVNC = () => {
  if (!vncScreen.value) return

  vncStatusText.value = 'Connecting...'
  vncStatusClass.value = 'connecting'

  try {
    rfb.value = new RFB(vncScreen.value, VNC_URL)

    rfb.value.addEventListener('connect', () => {
      isVNCConnected.value = true
      vncStatusText.value = 'Connected'
      vncStatusClass.value = 'connected'
      rfb.value.focus()
    })

    rfb.value.addEventListener('disconnect', (detail) => {
      isVNCConnected.value = false
      vncStatusText.value = 'Disconnected'
      vncStatusClass.value = 'disconnected'
      if (!detail.clean) {
        vncStatusText.value = 'Connection Lost'
        vncStatusClass.value = 'error'
      }
    })

  } catch (error) {
    console.error('VNC connection error:', error)
    vncStatusText.value = 'Error'
    vncStatusClass.value = 'error'
  }
}

const disconnectVNC = () => {
  if (rfb.value) {
    rfb.value.disconnect()
  }
}

onMounted(() => {
  // Auto-connect VNC (optional)
  // connectVNC()
})

onUnmounted(() => {
  disconnectVNC()
})
</script>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #121212;
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.app-header {
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #4caf50;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
  background: linear-gradient(45deg, #4caf50, #64b5f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.vnc-status {
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 500;
}

.vnc-status.connected { background: #4caf50; color: white; }
.vnc-status.disconnected { background: #666; color: #ccc; }
.vnc-status.connecting { background: #ff9800; color: white; }
.vnc-status.error { background: #f44336; color: white; }

.connect-btn, .small-btn {
  padding: 8px 16px;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.connect-btn:hover:not(:disabled),
.small-btn:hover:not(:disabled) {
  background: #45a049;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.4);
}

.connect-btn:disabled,
.small-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0;
  min-height: 0;
  overflow: hidden;
}

.left-panel, .middle-panel, .right-panel {
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  border-right: 1px solid #3d3d3d;
  min-height: 0;
}

.right-panel {
  border-right: none;
}

.panel-header {
  padding: 1rem;
  background: #2d2d2d;
  border-bottom: 1px solid #3d3d3d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #e0e0e0;
}

.left-tabs {
  display: flex;
  gap: 0.5rem;
}

.left-tab {
  padding: 0.5rem 1rem;
  background: transparent;
  color: #888;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.left-tab:hover {
  background: #333;
  color: #aaa;
}

.left-tab.active {
  background: #4caf50;
  color: white;
}

.vnc-controls {
  display: flex;
  gap: 0.5rem;
}

.monitor-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.small-btn {
  padding: 6px 12px;
  font-size: 0.85rem;
}

.vnc-container {
  flex: 1;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  position: relative;
}

.vnc-container :deep(canvas) {
  box-shadow: 0 0 20px rgba(0,0,0,0.5);
  max-width: 100%;
  max-height: 100%;
}

.tab-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tabs {
  display: flex;
  background: #2d2d2d;
  border-bottom: 1px solid #3d3d3d;
}

.tab {
  flex: 1;
  padding: 0.75rem 1rem;
  background: transparent;
  color: #888;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.tab:hover {
  background: #333;
  color: #aaa;
}

.tab.active {
  color: #4caf50;
  border-bottom-color: #4caf50;
  background: #252525;
}

.tab-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.tools-panel {
  padding: 2rem;
  text-align: center;
  color: #888;
}

/* Responsive */
@media (max-width: 1400px) {
  .main-content {
    grid-template-columns: 1fr 1fr;
  }
  
  .right-panel {
    grid-column: 1 / -1;
  }
}

@media (max-width: 900px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .left-panel, .middle-panel {
    min-height: 400px;
  }
}
</style>
