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
