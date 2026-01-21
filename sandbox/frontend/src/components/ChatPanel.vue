<template>
  <div class="chat-panel">
    <div class="chat-header">
      <h3>🤖 AI Agent</h3>
      <div class="connection-status" :class="{ connected: isConnected }">
        {{ isConnected ? 'Connected' : 'Disconnected' }}
      </div>
    </div>

    <div class="messages-container" ref="messagesContainer">
      <div v-if="messages.length === 0" class="welcome-message">
        <h4>👋 Hi! I'm your AI Sandbox Assistant</h4>
        <p>I can help you with:</p>
        <ul>
          <li>📁 File operations</li>
          <li>💻 Running shell commands</li>
          <li>🌐 Browser automation</li>
          <li>⭐ Installing new tools from MCP marketplace</li>
        </ul>
        <p class="tip">Try asking: "What tools do you have?" or "Show me the MCP marketplace"</p>
      </div>

      <div v-for="(msg, index) in messages" :key="index" 
           :class="['message', msg.role]">
        <div class="message-avatar">
          {{ msg.role === 'user' ? '👤' : '🤖' }}
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(msg.content)"></div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>

      <div v-if="isLoading" class="message assistant loading">
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <div class="input-container">
      <textarea
        v-model="inputMessage"
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.enter.shift.exact="inputMessage += '\n'"
        placeholder="Ask me anything... (Enter to send, Shift+Enter for new line)"
        :disabled="isLoading || !isConnected"
        rows="3"
      ></textarea>
      <button 
        @click="sendMessage" 
        :disabled="!inputMessage.trim() || isLoading || !isConnected"
        class="send-button"
      >
        <span v-if="!isLoading">Send</span>
        <span v-else>Sending...</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const isConnected = ref(false)
const messagesContainer = ref(null)

const API_URL = 'http://localhost:8000'

// Check backend connection
const checkConnection = async () => {
  try {
    const response = await fetch(`${API_URL}/health`)
    isConnected.value = response.ok
  } catch (error) {
    isConnected.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
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

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
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
  // Check connection every 5 seconds
  setInterval(checkConnection, 5000)
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  color: #e0e0e0;
}

.chat-header {
  padding: 1rem;
  background: #2d2d2d;
  border-bottom: 1px solid #3d3d3d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.connection-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  background: #555;
  color: #aaa;
}

.connection-status.connected {
  background: #4caf50;
  color: white;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.welcome-message {
  background: #2d2d2d;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 3px solid #4caf50;
}

.welcome-message h4 {
  margin: 0 0 1rem 0;
  color: #4caf50;
}

.welcome-message ul {
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.welcome-message li {
  margin: 0.5rem 0;
}

.tip {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #3d3d3d;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #aaa;
}

.message {
  display: flex;
  gap: 0.75rem;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: #1976d2;
}

.message.assistant .message-avatar {
  background: #4caf50;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-text {
  padding: 0.75rem 1rem;
  border-radius: 12px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message.user .message-text {
  background: #1976d2;
  color: white;
}

.message.assistant .message-text {
  background: #2d2d2d;
  color: #e0e0e0;
}

.message-text :deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.message-text :deep(a) {
  color: #64b5f6;
  text-decoration: underline;
}

.message-time {
  font-size: 0.7rem;
  color: #888;
  margin-top: 0.25rem;
  padding-left: 1rem;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 1rem;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4caf50;
  animation: bounce 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.input-container {
  padding: 1rem;
  background: #2d2d2d;
  border-top: 1px solid #3d3d3d;
  display: flex;
  gap: 0.75rem;
}

textarea {
  flex: 1;
  padding: 0.75rem;
  background: #1e1e1e;
  color: #e0e0e0;
  border: 1px solid #3d3d3d;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 0.9rem;
}

textarea:focus {
  outline: none;
  border-color: #4caf50;
}

textarea::placeholder {
  color: #666;
}

.send-button {
  padding: 0.75rem 1.5rem;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.send-button:hover:not(:disabled) {
  background: #45a049;
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Scrollbar styling */
.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #3d3d3d;
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #4d4d4d;
}
</style>
