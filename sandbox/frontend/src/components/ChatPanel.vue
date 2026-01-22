<template>
  <div class="chat-panel">
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
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.enter.shift.exact="adjustHeight"
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

const messages = ref([
  // 演示对话 - 展示工作流看板
  {
    role: 'user',
    content: '帮我调研最新的 AI 硬件发展趋势，并在 Sandbox 中整理出一份对比表。',
    timestamp: new Date()
  },
  {
    role: 'assistant',
    content: `<div class="workflow-response">
      <div class="workflow-status">
        <div class="status-icon-wrapper">
          <div class="status-icon-ring"></div>
          <div class="status-icon-dot"></div>
        </div>
        <p class="workflow-title">正在启动工作流：<span class="workflow-name">硬件趋势调研 2026</span></p>
      </div>

      <div class="workflow-board">
        <div class="workflow-board-header">
          <span class="board-title">AI WORKFLOW BOARD</span>
          <span class="board-status waiting">Waiting for Approval</span>
        </div>
        <div class="workflow-tasks">
          <div class="task-item active">
            <span class="task-text">01. 检索 2025-2026 发布的 AI 芯片</span>
            <button class="task-btn confirm">确认执行</button>
          </div>
          <div class="task-item pending">
            <span class="task-text">02. 提取性能对比参数</span>
            <span class="task-status">Pending</span>
          </div>
          <div class="task-item pending">
            <span class="task-text">03. 生成对比表格</span>
            <span class="task-status">Pending</span>
          </div>
        </div>
      </div>
    </div>`,
    timestamp: new Date(),
    isWorkflow: true
  }
])

const inputMessage = ref('')
const isLoading = ref(false)
const isConnected = ref(false)
const messagesContainer = ref(null)
const inputRef = ref(null)

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
.chat-panel {
  display: flex;
  flex-direction: column;
  /* height: 100%; removed to let flex parent control height */
  position: relative;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

/* Custom Scrollbar - Gemini Style */
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
  color: #e3e3e3;
  text-align: center;
  margin-top: -10%;
}

.welcome-logo {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.welcome-container h2 {
  font-size: 2rem;
  margin: 0 0 0.8rem 0;
  font-weight: 500;
  background: linear-gradient(70deg, #4285f4, #9b72cb);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: #aaa;
  margin-bottom: 3rem;
  max-width: 500px;
  font-size: 0.95rem;
}

.suggestions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}

.suggestion-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 1.2rem;
  border-radius: 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  width: 150px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #e3e3e3;
}

.suggestion-card:hover {
  background: rgba(66, 133, 244, 0.1);
  border-color: rgba(66, 133, 244, 0.3);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(66, 133, 244, 0.15);
}

.suggestion-card .icon {
  font-size: 1.8rem;
}

.suggestion-card .text {
  font-size: 0.85rem;
  opacity: 0.9;
}

/* Messages - Gemini Style */
.message-row {
  display: flex;
  gap: 1rem;
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

.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.message-row.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.message-row.assistant .message-avatar {
  background: linear-gradient(135deg, #4285f4 0%, #9b72cb 100%);
  border: none;
}

.message-bubble {
  flex: 1;
  max-width: 80%;
}

.message-row.user .message-bubble {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-name {
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 6px;
  font-weight: 500;
}

.message-content {
  line-height: 1.7;
  color: #e3e3e3;
  padding: 1rem 1.2rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.message-row.user .message-content {
  background: linear-gradient(135deg, rgba(66, 133, 244, 0.15), rgba(155, 114, 203, 0.1));
  border-color: rgba(66, 133, 244, 0.2);
  border-radius: 18px 18px 4px 18px;
}

.message-row.assistant .message-content {
  border-radius: 18px 18px 18px 4px;
}

/* Input Area - Gemini Style */
.input-area {
  padding: 1.5rem 2rem 2rem;
  background: var(--gemini-surface);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.input-wrapper {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 0.8rem 1.2rem;
  display: flex;
  align-items: flex-end;
  gap: 0.8rem;
  transition: all 0.3s;
  position: relative;
}

.input-wrapper:focus-within {
  border-color: rgba(66, 133, 244, 0.5);
  box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
  background: rgba(255, 255, 255, 0.05);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  resize: none;
  padding: 6px 0;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.5;
  max-height: 200px;
  outline: none;
}

textarea::placeholder {
  color: #666;
}

.send-btn {
  background: linear-gradient(135deg, #4285f4, #9b72cb);
  color: #fff;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.3s;
  font-size: 1.1rem;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(66, 133, 244, 0.4);
}

.send-btn:disabled {
  background: rgba(255, 255, 255, 0.05);
  color: #444;
  cursor: not-allowed;
  transform: none;
}

.input-footer {
  margin-top: 0.8rem;
  text-align: center;
  font-size: 0.75rem;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
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

/* Workflow Board Styles */
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
  border: 2px solid #4285f4;
  position: absolute;
  top: 0;
  left: 0;
}

.status-icon-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4285f4;
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
  color: #aaa;
  font-size: 0.95rem;
  margin: 0;
  line-height: 1.6;
}

.workflow-name {
  color: #4285f4;
  font-weight: 500;
}

.workflow-board {
  background: rgba(255, 255, 255, 0.03);
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
  color: #666;
}

.board-status {
  font-size: 11px;
  font-weight: 500;
}

.board-status.waiting {
  color: #ff9800;
}

.board-status.running {
  color: #4285f4;
}

.board-status.completed {
  color: #4caf50;
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
  border-radius: 0 8px 8px 0;
  transition: all 0.2s;
}

.task-item.active {
  border-left: 2px solid #4285f4;
  background: linear-gradient(90deg, rgba(66, 133, 244, 0.1) 0%, transparent 100%);
}

.task-item.pending {
  opacity: 0.4;
  border-left: 2px solid transparent;
}

.task-item.completed {
  opacity: 0.6;
  border-left: 2px solid #4caf50;
  background: linear-gradient(90deg, rgba(76, 175, 80, 0.05) 0%, transparent 100%);
}

.task-text {
  font-size: 0.9rem;
  color: #e3e3e3;
}

.task-btn {
  font-size: 10px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.task-btn.confirm {
  background: #4285f4;
  color: white;
}

.task-btn.confirm:hover {
  background: #5a95f5;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
}

.task-status {
  font-size: 10px;
  font-style: italic;
  color: #666;
}
</style>
