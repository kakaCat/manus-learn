<template>
  <div class="monitor-container">
    <!-- Status Overview -->
    <div class="status-section">
      <h4 class="section-title">📊 Sandbox Status</h4>
      <div class="status-grid">
        <div class="status-card" :class="statusClass">
          <div class="status-label">Container</div>
          <div class="status-value">{{ containerStatus }}</div>
        </div>
        <div class="status-card">
          <div class="status-label">MCP Servers</div>
          <div class="status-value">{{ mcpServerCount }}</div>
        </div>
        <div class="status-card">
          <div class="status-label">Processes</div>
          <div class="status-value">{{ processCount }}</div>
        </div>
      </div>
    </div>

    <!-- Resource Usage -->
    <div class="resource-section">
      <h4 class="section-title">💻 Resource Usage</h4>
      <div v-if="resources" class="resource-bars">
        <div class="resource-item">
          <div class="resource-header">
            <span>CPU</span>
            <span class="resource-percent">{{ resources.cpu }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill cpu" :style="{ width: resources.cpu + '%' }"></div>
          </div>
        </div>
        <div class="resource-item">
          <div class="resource-header">
            <span>Memory</span>
            <span class="resource-percent">{{ resources.memory }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill memory" :style="{ width: resources.memory + '%' }"></div>
          </div>
        </div>
        <div class="resource-item">
          <div class="resource-header">
            <span>Disk</span>
            <span class="resource-percent">{{ resources.disk }}</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill disk" :style="{ width: parseDiskUsage(resources.disk) + '%' }"></div>
          </div>
        </div>
      </div>
      <div v-else class="loading">Loading resources...</div>
    </div>

    <!-- MCP Servers -->
    <div class="mcp-section">
      <h4 class="section-title">🔧 MCP Servers</h4>
      <div v-if="mcpServers.length > 0" class="mcp-list">
        <div v-for="server in mcpServers" :key="server.name" class="mcp-item">
          <div class="mcp-icon" :class="server.status">●</div>
          <div class="mcp-info">
            <div class="mcp-name">{{ server.name }}</div>
            <div class="mcp-status">{{ server.status }} • PID {{ server.pid }}</div>
          </div>
        </div>
      </div>
      <div v-else class="loading">Loading MCP servers...</div>
    </div>

    <!-- Running Processes -->
    <div class="process-section">
      <h4 class="section-title">⚙️ Running Processes (Top 10)</h4>
      <div v-if="processes.length > 0" class="process-list">
        <div v-for="process in processes.slice(0, 10)" :key="process.pid" class="process-item">
          <div class="process-pid">{{ process.pid }}</div>
          <div class="process-name">{{ process.name }}</div>
          <div class="process-cpu">{{ process.cpu }}%</div>
          <div class="process-mem">{{ process.memory }}%</div>
        </div>
      </div>
      <div v-else class="loading">Loading processes...</div>
    </div>

    <!-- Logs -->
    <div class="logs-section">
      <h4 class="section-title">📝 Recent Logs</h4>
      <div class="logs-container">
        <pre v-if="logs" class="logs-text">{{ logs }}</pre>
        <div v-else class="loading">Loading logs...</div>
      </div>
    </div>

    <!-- Auto-refresh indicator -->
    <div class="refresh-indicator">
      Auto-refreshing every {{ refreshInterval / 1000 }}s
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const API_URL = 'http://localhost:8000'

// State
const containerStatus = ref('Unknown')
const statusClass = ref('status-unknown')
const mcpServerCount = ref(0)
const processCount = ref(0)
const resources = ref(null)
const mcpServers = ref([])
const processes = ref([])
const logs = ref('')

// Refresh interval (5 seconds)
const refreshInterval = 5000
let refreshTimer = null

// Parse MCP status output
const parseMcpStatus = (statusText) => {
  const servers = []
  const lines = statusText.split('\n')

  for (const line of lines) {
    if (line.includes('RUNNING') || line.includes('STOPPED') || line.includes('FATAL')) {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 3) {
        const name = parts[0]
        const status = parts[1]
        const pidMatch = line.match(/pid (\d+)/)
        const pid = pidMatch ? pidMatch[1] : 'N/A'

        servers.push({
          name,
          status: status.toLowerCase(),
          pid
        })
      }
    }
  }

  return servers
}

// Parse process output
const parseProcesses = (processText) => {
  const processList = []

  try {
    const lines = processText.split('\n').filter(l => l.trim())

    for (const line of lines) {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 4 && !isNaN(parts[0])) {
        processList.push({
          pid: parts[0],
          name: parts[1],
          cpu: parseFloat(parts[2]) || 0,
          memory: parseFloat(parts[3]) || 0
        })
      }
    }

    // Sort by CPU usage
    processList.sort((a, b) => b.cpu - a.cpu)
  } catch (e) {
    console.error('Error parsing processes:', e)
  }

  return processList
}

// Parse resource output
const parseResources = (resourceText) => {
  try {
    const lines = resourceText.split('\n').filter(l => l.trim())
    const cpu = parseFloat(lines[1]) || 0
    const memory = parseFloat(lines[3]) || 0
    const disk = lines[5] || '0%'

    return {
      cpu: cpu.toFixed(1),
      memory: memory.toFixed(1),
      disk: disk.trim()
    }
  } catch (e) {
    console.error('Error parsing resources:', e)
    return { cpu: 0, memory: 0, disk: '0%' }
  }
}

// Parse disk usage percentage
const parseDiskUsage = (diskStr) => {
  const match = diskStr.match(/(\d+)%/)
  return match ? parseInt(match[1]) : 0
}

// Fetch sandbox status
const fetchStatus = async () => {
  try {
    const response = await fetch(`${API_URL}/api/sandbox/status`)
    const data = await response.json()

    if (data.status === 'running') {
      containerStatus.value = 'Running'
      statusClass.value = 'status-running'

      // Parse MCP status
      if (data.mcp_status) {
        const servers = parseMcpStatus(data.mcp_status)
        mcpServers.value = servers
        mcpServerCount.value = servers.filter(s => s.status === 'running').length
      }
    } else {
      containerStatus.value = 'Error'
      statusClass.value = 'status-error'
    }
  } catch (error) {
    console.error('Error fetching status:', error)
    containerStatus.value = 'Disconnected'
    statusClass.value = 'status-error'
  }
}

// Fetch processes
const fetchProcesses = async () => {
  try {
    const response = await fetch(`${API_URL}/api/sandbox/processes`)
    const data = await response.json()

    if (data.status === 'success' && data.processes) {
      const parsed = parseProcesses(data.processes)
      processes.value = parsed
      processCount.value = parsed.length
    }
  } catch (error) {
    console.error('Error fetching processes:', error)
  }
}

// Fetch resources
const fetchResources = async () => {
  try {
    const response = await fetch(`${API_URL}/api/sandbox/resources`)
    const data = await response.json()

    if (data.status === 'success' && data.resources) {
      resources.value = parseResources(data.resources)
    }
  } catch (error) {
    console.error('Error fetching resources:', error)
  }
}

// Fetch logs
const fetchLogs = async () => {
  try {
    const response = await fetch(`${API_URL}/api/sandbox/logs`)
    const data = await response.json()

    if (data.status === 'success' && data.logs) {
      logs.value = data.logs
    }
  } catch (error) {
    console.error('Error fetching logs:', error)
  }
}

// Fetch all data
const fetchAllData = async () => {
  await Promise.all([
    fetchStatus(),
    fetchProcesses(),
    fetchResources(),
    fetchLogs()
  ])
}

onMounted(async () => {
  // Initial fetch
  await fetchAllData()

  // Set up auto-refresh
  refreshTimer = setInterval(fetchAllData, refreshInterval)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.monitor-container {
  height: 100%;
  overflow-y: auto;
  padding: 1rem;
  background: #1e1e1e;
  color: #e0e0e0;
}

.section-title {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #4caf50;
  border-bottom: 1px solid #3d3d3d;
  padding-bottom: 0.5rem;
}

/* Status Section */
.status-section {
  margin-bottom: 1.5rem;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.status-card {
  background: #2d2d2d;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #3d3d3d;
}

.status-card.status-running {
  border-color: #4caf50;
  box-shadow: 0 0 10px rgba(76, 175, 80, 0.2);
}

.status-card.status-error {
  border-color: #f44336;
  box-shadow: 0 0 10px rgba(244, 67, 54, 0.2);
}

.status-label {
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.status-value {
  font-size: 1.2rem;
  font-weight: 600;
  color: #e0e0e0;
}

/* Resource Section */
.resource-section {
  margin-bottom: 1.5rem;
}

.resource-bars {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.resource-item {
  background: #2d2d2d;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #3d3d3d;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.resource-percent {
  font-weight: 600;
  color: #4caf50;
}

.progress-bar {
  height: 8px;
  background: #1a1a1a;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.5s ease;
  border-radius: 4px;
}

.progress-fill.cpu {
  background: linear-gradient(90deg, #4caf50, #8bc34a);
}

.progress-fill.memory {
  background: linear-gradient(90deg, #2196f3, #64b5f6);
}

.progress-fill.disk {
  background: linear-gradient(90deg, #ff9800, #ffb74d);
}

/* MCP Section */
.mcp-section {
  margin-bottom: 1.5rem;
}

.mcp-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.mcp-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #2d2d2d;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  border: 1px solid #3d3d3d;
}

.mcp-icon {
  font-size: 1.5rem;
  width: 20px;
  text-align: center;
}

.mcp-icon.running {
  color: #4caf50;
}

.mcp-icon.stopped {
  color: #666;
}

.mcp-icon.fatal {
  color: #f44336;
}

.mcp-info {
  flex: 1;
}

.mcp-name {
  font-weight: 500;
  color: #e0e0e0;
  font-size: 0.95rem;
}

.mcp-status {
  font-size: 0.8rem;
  color: #888;
  margin-top: 0.25rem;
}

/* Process Section */
.process-section {
  margin-bottom: 1.5rem;
}

.process-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
}

.process-item {
  display: grid;
  grid-template-columns: 60px 1fr 60px 60px;
  gap: 1rem;
  background: #2d2d2d;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: 1px solid #3d3d3d;
  font-size: 0.85rem;
}

.process-pid {
  color: #888;
}

.process-name {
  color: #e0e0e0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.process-cpu,
.process-mem {
  text-align: right;
  color: #4caf50;
  font-family: monospace;
}

/* Logs Section */
.logs-section {
  margin-bottom: 1rem;
}

.logs-container {
  background: #1a1a1a;
  border: 1px solid #3d3d3d;
  border-radius: 6px;
  padding: 1rem;
  max-height: 300px;
  overflow-y: auto;
}

.logs-text {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  color: #aaa;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Loading */
.loading {
  text-align: center;
  padding: 2rem;
  color: #888;
  font-style: italic;
}

/* Refresh Indicator */
.refresh-indicator {
  text-align: center;
  padding: 0.5rem;
  font-size: 0.75rem;
  color: #666;
  font-style: italic;
}

/* Scrollbar styling */
.monitor-container::-webkit-scrollbar,
.process-list::-webkit-scrollbar,
.logs-container::-webkit-scrollbar {
  width: 8px;
}

.monitor-container::-webkit-scrollbar-track,
.process-list::-webkit-scrollbar-track,
.logs-container::-webkit-scrollbar-track {
  background: #1a1a1a;
}

.monitor-container::-webkit-scrollbar-thumb,
.process-list::-webkit-scrollbar-thumb,
.logs-container::-webkit-scrollbar-thumb {
  background: #3d3d3d;
  border-radius: 4px;
}

.monitor-container::-webkit-scrollbar-thumb:hover,
.process-list::-webkit-scrollbar-thumb:hover,
.logs-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
