<template>
  <div class="mcp-marketplace">
    <div class="marketplace-header">
      <h3>📦 MCP Marketplace</h3>
      <button @click="refreshMarketplace" :disabled="isLoading" class="refresh-btn">
        🔄 Refresh
      </button>
    </div>

    <div class="filter-bar">
      <select v-model="selectedCategory" class="category-filter">
        <option value="">All Categories</option>
        <option value="浏览器">🌐 Browser</option>
        <option value="搜索">🔍 Search</option>
        <option value="工具">🛠️ Tools</option>
        <option value="文件操作">📁 Files</option>
      </select>
      
      <div class="stats">
        <span>{{ installedCount }} installed</span>
        <span>|</span>
        <span>{{ availableCount }} available</span>
      </div>
    </div>

    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
      <p>Loading marketplace...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <p>❌ {{ error }}</p>
      <button @click="refreshMarketplace">Try Again</button>
    </div>

    <div v-else class="mcp-grid">
      <div v-for="mcp in filteredMCPs" :key="mcp.id" 
           :class="['mcp-card', { installed: mcp.installed }]">
        <div class="card-header">
          <h4>{{ mcp.name }}</h4>
          <span class="badge" :class="{ official: mcp.official }">
            {{ mcp.official ? '🏅 Official' : '👥 Community' }}
          </span>
        </div>

        <div class="card-body">
          <p class="description">{{ mcp.description }}</p>
          
          <div class="capabilities" v-if="mcp.capabilities && mcp.capabilities.length">
            <strong>Capabilities:</strong>
            <div class="capability-tags">
              <span v-for="cap in mcp.capabilities" :key="cap" class="tag">
                {{ cap }}
              </span>
            </div>
          </div>

          <div class="card-footer">
            <div class="category-badge">{{ mcp.category }}</div>
            
            <button 
              v-if="!mcp.installed"
              @click="installMCP(mcp.id)"
              :disabled="installing === mcp.id"
              class="install-btn"
            >
              <span v-if="installing === mcp.id">Installing...</span>
              <span v-else>📥 Install</span>
            </button>
            
            <div v-else class="installed-badge">
              ✅ Installed
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const mcps = ref([])
const isLoading = ref(false)
const error = ref(null)
const selectedCategory = ref('')
const installing = ref(null)

const API_URL = 'http://localhost:8000'

const installedCount = computed(() => 
  mcps.value.filter(m => m.installed).length
)

const availableCount = computed(() => mcps.value.length)

const filteredMCPs = computed(() => {
  if (!selectedCategory.value) return mcps.value
  return mcps.value.filter(m => m.category === selectedCategory.value)
})

const refreshMarketplace = async () => {
  isLoading.value = true
  error.value = null

  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: "List all available MCPs in the marketplace with their details",
        chat_history: []
      })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    
    // Parse the AI response to extract MCP list
    // This is a simplified version - you might want to add proper parsing
    const mockMCPs = [
      {
        id: 'filesystem',
        name: 'Filesystem MCP',
        description: '官方文件系统操作服务器 - 提供文件读写、目录管理等功能',
        category: '文件操作',
        official: true,
        installed: true,
        capabilities: ['read_file', 'write_file', 'list_directory']
      },
      {
        id: 'chrome',
        name: 'Chrome DevTools MCP',
        description: 'Chrome 官方浏览器自动化服务器 - 基于 Puppeteer 的强大浏览器控制',
        category: '浏览器',
        official: true,
        installed: true,
        capabilities: ['navigate', 'screenshot', 'click', 'fill_form']
      },
      {
        id: 'memory',
        name: 'Memory MCP',
        description: '官方记忆存储服务器 - 为 AI 提供持久化记忆能力',
        category: '工具',
        official: true,
        installed: true,
        capabilities: ['store_memory', 'recall_memory']
      },
      {
        id: 'brave-search',
        name: 'Brave Search MCP',
        description: 'Brave 搜索引擎集成 - 隐私友好的网络搜索',
        category: '搜索',
        official: true,
        installed: false,
        capabilities: ['web_search']
      },
      {
        id: 'puppeteer',
        name: 'Puppeteer MCP',
        description: '官方 Puppeteer 浏览器自动化 - 完整的浏览器控制能力',
        category: '浏览器',
        official: true,
        installed: false,
        capabilities: ['browser_automation', 'web_scraping']
      }
    ]

    mcps.value = mockMCPs

  } catch (err) {
    console.error('Marketplace error:', err)
    error.value = `Failed to load marketplace: ${err.message}`
  } finally {
    isLoading.value = false
  }
}

const installMCP = async (mcpId) => {
  installing.value = mcpId

  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `Install the MCP with id: ${mcpId}`,
        chat_history: []
      })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    
    alert(`✅ Installation initiated!\n\n${data.response}\n\nPlease restart the container:\ncd sandbox && docker-compose restart`)
    
    // Mark as installed locally
    const mcp = mcps.value.find(m => m.id === mcpId)
    if (mcp) mcp.installed = true

  } catch (err) {
    console.error('Install error:', err)
    alert(`❌ Failed to install: ${err.message}`)
  } finally {
    installing.value = null
  }
}

onMounted(() => {
  refreshMarketplace()
})
</script>

<style scoped>
.mcp-marketplace {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  color: #e0e0e0;
}

.marketplace-header {
  padding: 1rem;
  background: #2d2d2d;
  border-bottom: 1px solid #3d3d3d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.marketplace-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.refresh-btn {
  padding: 0.5rem 1rem;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.refresh-btn:hover:not(:disabled) {
  background: #45a049;
}

.filter-bar {
  padding: 1rem;
  background: #252525;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #3d3d3d;
}

.category-filter {
  padding: 0.5rem;
  background: #2d2d2d;
  color: #e0e0e0;
  border: 1px solid #3d3d3d;
  border-radius: 6px;
  cursor: pointer;
}

.stats {
  font-size: 0.9rem;
  color: #888;
  display: flex;
  gap: 0.5rem;
}

.loading, .error-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #3d3d3d;
  border-top-color: #4caf50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.mcp-grid {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  align-content: start;
}

.mcp-card {
  background: #2d2d2d;
  border: 1px solid #3d3d3d;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.mcp-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.mcp-card.installed {
  border-color: #4caf50;
}

.card-header {
  padding: 1rem;
  background: #252525;
  border-bottom: 1px solid #3d3d3d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h4 {
  margin: 0;
  font-size: 1rem;
}

.badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  background: #3d3d3d;
}

.badge.official {
  background: #1976d2;
  color: white;
}

.card-body {
  padding: 1rem;
}

.description {
  margin: 0 0 1rem 0;
  font-size: 0.9rem;
  line-height: 1.5;
  color: #aaa;
}

.capabilities {
  margin: 1rem 0;
  font-size: 0.85rem;
}

.capability-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.tag {
  padding: 4px 8px;
  background: #3d3d3d;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #aaa;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #3d3d3d;
}

.category-badge {
  padding: 4px 12px;
  background: #3d3d3d;
  border-radius: 12px;
  font-size: 0.8rem;
  color: #aaa;
}

.install-btn {
  padding: 0.5rem 1rem;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}

.install-btn:hover:not(:disabled) {
  background: #45a049;
}

.install-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.installed-badge {
  padding: 0.5rem 1rem;
  background: #2e7d32;
  color: white;
  border-radius: 6px;
  font-size: 0.85rem;
}

/* Scrollbar */
.mcp-grid::-webkit-scrollbar {
  width: 8px;
}

.mcp-grid::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.mcp-grid::-webkit-scrollbar-thumb {
  background: #3d3d3d;
  border-radius: 4px;
}
</style>
