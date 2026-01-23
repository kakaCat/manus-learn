<template>
  <div class="chat-panel">
    <!-- Chat Header with Actions -->
    <div class="chat-header">
      <div class="session-info">
        <span class="status-indicator" :class="{ connected: isConnected }"></span>
        <span class="session-title">Current Session</span>
        <span v-if="currentThreadId" class="session-id" :title="currentThreadId">#{{ currentThreadId.slice(0, 8) }}</span>
        <span v-if="sessionCount > 0" class="session-count">({{ sessionCount }} active)</span>
      </div>
      <div class="chat-actions">
        <button 
          @click="clearHistory" 
          class="action-btn" 
          title="Clear Chat History"
          :disabled="isLoading || messages.length === 0"
        >
          🗑️ Clear
        </button>
      </div>
    </div>

    <div class="messages-container" ref="messagesContainer">
      <div v-if="messages.length === 0" class="welcome-container">
        <div class="welcome-logo">🤖</div>
        <h2>How can I help you today?</h2>
        <p class="subtitle">I can help you execute code, browse the web, and manage files in the sandbox.</p>
        
        <div class="suggestions">
          <button @click="setInput('Check system status')" class="suggestion-card">
            <span class="icon">📊</span>
            <span class="text">Check system status</span>
          </button>
          <button @click="setInput('List files in current directory')" class="suggestion-card">
            <span class="icon">📂</span>
            <span class="text">List files</span>
          </button>
          <button @click="setInput('Open a browser to google.com')" class="suggestion-card">
            <span class="icon">🌐</span>
            <span class="text">Open Browser</span>
          </button>
        </div>
      </div>

      <div v-for="(msg, index) in messages" :key="index" 
           :class="['message-row', msg.role]">
        <div class="message-avatar">
          {{ msg.role === 'user' ? '👤' : '🤖' }}
        </div>
        <div class="message-bubble">
          <div class="message-name">{{ msg.role === 'user' ? 'You' : 'Manus' }}</div>
          <div class="message-content" v-html="formatMessage(msg.content)"></div>
          <!-- <div class="message-time">{{ formatTime(msg.timestamp) }}</div> -->
        </div>
      </div>

      <div v-if="isLoading" class="message-row assistant loading">
        <div class="message-avatar">🤖</div>
        <div class="message-bubble">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-wrapper">
        <textarea
          v-model="inputMessage"
          ref="inputRef"
          @keydown.enter.exact.prevent="handleEnter"
          @keydown.enter.shift.exact="adjustHeight"
          @compositionstart="isComposing = true"
          @compositionend="isComposing = false"
          @input="adjustHeight"
          placeholder="Message Manus..."
          :disabled="isLoading || !isConnected"
          rows="1"
        ></textarea>
        <button 
          @click="sendMessage" 
          :disabled="!inputMessage.trim() || isLoading || !isConnected"
          class="send-btn"
          title="Send Message"
        >
          ➤
        </button>
      </div>
      <div class="input-footer">
        <span class="status-dot" :class="{ connected: isConnected }"></span>
        {{ isConnected ? 'AI Ready' : 'Connecting...' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'

const messages = ref([])

const inputMessage = ref('')
const isLoading = ref(false)
const isConnected = ref(false)
const sessionCount = ref(0)
const sessions = ref([])
const currentThreadId = ref(null)
const messagesContainer = ref(null)
const inputRef = ref(null)

const API_URL = 'http://localhost:8000'

// Check backend connection
const checkConnection = async () => {
  try {
    const response = await fetch(`${API_URL}/`)
    isConnected.value = response.ok
    if (isConnected.value) {
      fetchSessions()
    }
  } catch (error) {
    isConnected.value = false
  }
}

const fetchSessions = async () => {
  try {
    const response = await fetch(`${API_URL}/api/chat/sessions`)
    if (response.ok) {
      const data = await response.json()
      sessionCount.value = data.total_sessions
      sessions.value = data.sessions
    }
  } catch (error) {
    console.error('Error fetching sessions:', error)
  }
}

const clearHistory = async () => {
  if (!confirm('Are you sure you want to clear the chat history?')) return

  try {
    const url = currentThreadId.value 
      ? `${API_URL}/api/chat/clear?session_id=${currentThreadId.value}`
      : `${API_URL}/api/chat/clear`

    const response = await fetch(url, {
      method: 'POST'
    })
    
    if (response.ok) {
      messages.value = []
      currentThreadId.value = null
      // Add a system message
      messages.value.push({
        role: 'assistant',
        content: 'Chat history has been cleared.',
        timestamp: new Date()
      })
      fetchSessions()
    }
  } catch (error) {
    console.error('Error clearing history:', error)
    alert('Failed to clear history')
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const adjustHeight = () => {
  nextTick(() => {
    const el = inputRef.value
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 200) + 'px'
    }
  })
}

const setInput = (text) => {
  inputMessage.value = text
  if (inputRef.value) inputRef.value.focus()
}

const formatMessage = (content) => {
  // Convert markdown-like formatting to HTML
  let formatted = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
  
  // Convert URLs to links
  formatted = formatted.replace(
    /(https?:\/\/[^\s]+)/g,
    '<a href="$1" target="_blank">$1</a>'
  )
  
  return formatted
}

const handleEnter = (e) => {
  if (isComposing.value) return
  sendMessage()
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value || !isConnected.value) return

  const userMessage = {
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const currentInput = inputMessage.value
  inputMessage.value = ''
  
  // Reset height
  if (inputRef.value) inputRef.value.style.height = 'auto'

  isLoading.value = true
  scrollToBottom()

  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: currentInput,
        chat_history: messages.value.slice(-10).map(msg => ({
          role: msg.role === 'user' ? 'human' : 'ai',
          content: msg.content
        }))
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()

    messages.value.push({
      role: 'assistant',
      content: data.response || data.message || 'No response',
      timestamp: new Date()
    })

  } catch (error) {
    console.error('Chat error:', error)
    messages.value.push({
      role: 'assistant',
      content: `❌ Error: ${error.message}. Make sure the backend is running at ${API_URL}`,
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// Auto-scroll when new messages arrive
watch(() => messages.value.length, () => {
  scrollToBottom()
})

onMounted(() => {
  checkConnection()
  setInterval(checkConnection, 5000)
})
</script>

<style scoped>
/* Manus AI Style Refinement */
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  overflow: hidden;
  background-color: #09090b; /* Zinc 950 - Darker background */
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: transparent;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  z-index: 10;
}

.session-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: #a1a1aa; /* Zinc 400 */
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #ef4444;
  transition: all 0.3s;
}

.status-indicator.connected {
  background-color: #10b981; /* Emerald 500 */
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
}

.session-title {
  font-weight: 500;
  color: #e4e4e7; /* Zinc 200 */
  letter-spacing: -0.01em;
}

.session-id {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #71717a; /* Zinc 500 */
}

.action-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #a1a1aa;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.15);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 20%; /* Centered content with wide margins */
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Scrollbar styling */
.messages-container::-webkit-scrollbar {
  width: 6px;
}
.messages-container::-webkit-scrollbar-track {
  background: transparent;
}
.messages-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

/* Welcome Screen */
.welcome-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #e4e4e7;
  text-align: center;
  margin-top: -5%;
}

.welcome-logo {
  font-size: 3.5rem;
  margin-bottom: 2rem;
  position: relative;
}

.welcome-logo::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  z-index: -1;
  border-radius: 50%;
  filter: blur(20px);
}

.welcome-container h2 {
  font-size: 1.75rem;
  margin: 0 0 1rem 0;
  font-weight: 600;
  letter-spacing: -0.02em;
  background: linear-gradient(to bottom right, #fff, #a1a1aa);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: #71717a; /* Zinc 500 */
  margin-bottom: 3rem;
  max-width: 450px;
  font-size: 0.95rem;
  line-height: 1.6;
}

.suggestions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 800px;
}

.suggestion-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 1rem 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.8rem;
  transition: all 0.2s ease;
  color: #d4d4d8;
  min-width: 180px;
}

.suggestion-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.suggestion-card .icon {
  font-size: 1.2rem;
  opacity: 0.8;
}

.suggestion-card .text {
  font-size: 0.9rem;
  font-weight: 500;
}

/* Messages */
.message-row {
  display: flex;
  gap: 1.5rem;
  animation: fadeIn 0.4s ease-out;
  max-width: 100%;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 6px; /* Squircle */
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
  margin-top: 4px;
}

.message-row.assistant .message-avatar {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.message-bubble {
  flex: 1;
  max-width: 100%;
}

.message-name {
  font-size: 0.75rem;
  color: #71717a;
  margin-bottom: 0.5rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.message-content {
  line-height: 1.7;
  color: #e4e4e7;
  font-size: 0.95rem;
}

/* Assistant Message Styling */
.message-row.assistant .message-content {
  background: transparent;
  padding: 0;
  border: none;
}

/* User Message Styling */
.message-row.user {
  flex-direction: row-reverse;
}

.message-row.user .message-content {
  background: #27272a; /* Zinc 800 */
  padding: 0.75rem 1.25rem;
  border-radius: 12px;
  color: #fff;
}

/* Input Area - Floating Capsule Style */
.input-area {
  padding: 0 20% 2rem; /* Matches messages container padding */
  background: transparent; /* Transparent background */
  position: relative;
  z-index: 20;
}

.input-wrapper {
  background: rgba(39, 39, 42, 0.6); /* Zinc 800 with opacity */
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: flex-end;
  gap: 0.8rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.input-wrapper:focus-within {
  border-color: rgba(255, 255, 255, 0.15);
  background: rgba(39, 39, 42, 0.8);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  resize: none;
  padding: 8px 0;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.5;
  max-height: 200px;
  outline: none;
}

textarea::placeholder {
  color: #71717a;
}

.send-btn {
  background: #fff;
  color: #000;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
  font-size: 1rem;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 10px rgba(255, 255, 255, 0.2);
}

.send-btn:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.3);
  cursor: not-allowed;
}

.input-footer {
  margin-top: 1rem;
  text-align: center;
  font-size: 0.7rem;
  color: #52525b; /* Zinc 600 */
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #444;
  transition: all 0.3s;
}

.status-dot.connected {
  background: #4285f4;
  box-shadow: 0 0 8px rgba(66, 133, 244, 0.6);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  background: linear-gradient(135deg, #4285f4, #9b72cb);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* Code & Links Styling */
.message-content :deep(code) {
  background: rgba(66, 133, 244, 0.1);
  color: #4fc3f7;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.9em;
}

.message-content :deep(strong) {
  color: #fff;
  font-weight: 600;
}

.message-content :deep(a) {
  color: #4285f4;
  text-decoration: none;
  border-bottom: 1px solid rgba(66, 133, 244, 0.3);
  transition: border-color 0.2s;
}

.message-content :deep(a:hover) {
  border-bottom-color: #4285f4;
}

/* Workflow Board Styles - Refined */
.workflow-response {
  width: 100%;
}

.workflow-status {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.status-icon-wrapper {
  position: relative;
  width: 24px;
  height: 24px;
  margin-top: 2px;
  flex-shrink: 0;
}

.status-icon-ring {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid #3b82f6; /* Blue 500 */
  position: absolute;
  top: 0;
  left: 0;
}

.status-icon-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes ping {
  75%, 100% {
    transform: translate(-50%, -50%) scale(2);
    opacity: 0;
  }
}

.workflow-title {
  color: #a1a1aa;
  font-size: 0.95rem;
  margin: 0;
  line-height: 1.6;
}

.workflow-name {
  color: #60a5fa; /* Blue 400 */
  font-weight: 500;
}

.workflow-board {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 1rem;
  margin-top: 1rem;
}

.workflow-board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 0.75rem;
}

.board-title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #71717a;
}

.board-status {
  font-size: 11px;
  font-weight: 500;
}

.board-status.waiting {
  color: #fbbf24; /* Amber 400 */
}

.board-status.running {
  color: #60a5fa;
}

.board-status.completed {
  color: #34d399; /* Emerald 400 */
}

.workflow-tasks {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 6px;
  transition: all 0.2s;
  border-left: 2px solid transparent;
}

.task-item.active {
  border-left-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.task-item.pending {
  opacity: 0.5;
}

.task-item.completed {
  opacity: 0.8;
  border-left-color: #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.task-text {
  font-size: 0.9rem;
  color: #e4e4e7;
}

.task-btn {
  font-size: 10px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.task-btn.confirm {
  background: #3b82f6;
  color: white;
}

.task-btn.confirm:hover {
  background: #2563eb;
}

.task-status {
  font-size: 10px;
  font-family: 'JetBrains Mono', monospace;
  color: #71717a;
}
</style>
