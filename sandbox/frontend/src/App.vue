<template>
  <div class="h-screen flex overflow-hidden p-6 gap-6">
    <!-- Gemini 呼吸发光背景 -->
    <div class="gemini-glow"></div>

    <!-- 左侧聊天面板 -->
    <main class="flex-[6] flex flex-col glass-panel overflow-hidden shadow-2xl relative z-10">
      <div class="p-6 border-b border-white/5 flex items-center justify-between flex-shrink-0">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center">
            <span class="text-white text-lg">🤖</span>
          </div>
          <span class="font-medium text-lg">Manus <span class="text-gray-500 text-sm italic">AI Sandbox</span></span>
        </div>
        <span class="text-xs bg-white/10 px-3 py-1 rounded-full text-blue-300 font-mono tracking-widest">COLLABORATIVE MODE</span>
      </div>

      <ChatPanel class="flex-1 min-h-0" />
    </main>

    <!-- 右侧辅助面板 (VNC & Tools) -->
    <section class="flex-[6] relative z-10">
      <AuxiliaryPanel />
    </section>
  </div>
</template>

<script setup>
import ChatPanel from './components/ChatPanel.vue'
import AuxiliaryPanel from './components/AuxiliaryPanel.vue'
</script>

<style>
/* Gemini 风格配置 */
:root {
  --gemini-bg: #131314;
  --gemini-surface: #1e1f20;
  --gemini-gradient: linear-gradient(70deg, #4285f4, #9b72cb, #d96570);
}

body {
  background-color: var(--gemini-bg);
  color: #e3e3e3;
  font-family: 'Google Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  margin: 0;
  padding: 0;
}

/* Gemini 呼吸发光背景 */
.gemini-glow {
  background: var(--gemini-gradient);
  filter: blur(80px);
  opacity: 0.15;
  position: fixed;
  top: -10%;
  right: -10%;
  width: 40%;
  height: 40%;
  z-index: -1;
  animation: breathe 8s ease-in-out infinite;
}

@keyframes breathe {
  0%, 100% { opacity: 0.15; transform: scale(1); }
  50% { opacity: 0.25; transform: scale(1.1); }
}

/* 玻璃态面板 */
.glass-panel {
  background: var(--gemini-surface);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
}

/* 任务节点激活状态 */
.node-active {
  border-left: 2px solid #4285f4;
  background: linear-gradient(90deg, rgba(66, 133, 244, 0.1) 0%, transparent 100%);
}

* {
  box-sizing: border-box;
}
</style>
