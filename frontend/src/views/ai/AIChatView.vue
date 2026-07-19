<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import gsap from 'gsap'
import api from '@/api'

// 对话历史（仅浏览器内存，刷新即清空，不落库）
// 每条结构：{ role: 'user' | 'assistant', content: string }
const messages = ref([
  { role: 'assistant', content: '我在这里。想说什么都可以，不用整理好情绪再来。' },
])

const input = ref('')
const loading = ref(false)

// 简易 toast
const toastVisible = ref(false)
const toastText = ref('')
let toastTimer = null
const showToast = (text) => {
  toastText.value = text
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, 2400)
}

// 聊天滚动容器
const scrollRef = ref(null)
const inputRef = ref(null)

// 滚到底部
const scrollToBottom = async () => {
  await nextTick()
  const el = scrollRef.value
  if (el) {
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }
}

// textarea 自动撑高
const autoGrow = () => {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

// 键盘：Enter 发送，Shift+Enter 换行
const onKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    send()
  }
}

// 发送消息
const send = async () => {
  const text = input.value.trim()
  if (!text || loading.value) return

  // 1. 加入用户消息
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  // 重置 textarea 高度
  nextTick(() => {
    if (inputRef.value) inputRef.value.style.height = 'auto'
  })
  await scrollToBottom()

  // 2. 进入 loading 态
  loading.value = true
  await scrollToBottom()

  // 3. 调 AI 端点（超时 60s，由 axios 实例统一配置）
  try {
    const res = await api.post('/ai/chat', {
      messages: messages.value
        .filter((m) => m.content) // 过滤空内容
        .map((m) => ({ role: m.role, content: m.content })),
      scene: 'treehole',
    })

    // 兼容返回：{ reply, model, available } 或 { data: {...} }
    const data = res && res.data ? res.data : res
    const available = data?.available !== false
    const reply = data?.reply || ''

    if (!available) {
      // 降级：AI 不在岛上
      showToast('AI 暂时不在岛上')
      return
    }

    if (reply) {
      messages.value.push({ role: 'assistant', content: reply })
    } else {
      showToast('AI 没有回声，再试一次吧')
    }
  } catch (e) {
    showToast(e.message || '海风停了一下，再试一次吧')
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

// GSAP 入场动画
onMounted(() => {
  nextTick(() => {
    gsap.from('.chat-header', { y: -16, opacity: 0, duration: 0.6, ease: 'power2.out' })
    gsap.from('.chat-privacy', {
      y: -8,
      opacity: 0,
      duration: 0.6,
      ease: 'power2.out',
      delay: 0.1,
    })
    gsap.from('.msg-row', {
      y: 14,
      opacity: 0,
      duration: 0.5,
      ease: 'power3.out',
      stagger: 0.08,
      delay: 0.15,
    })
    gsap.from('.chat-input-wrap', {
      y: 20,
      opacity: 0,
      duration: 0.6,
      ease: 'power3.out',
      delay: 0.25,
    })
    scrollToBottom()
  })
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="chat-view">
    <!-- 顶部标题 + 隐私提示 -->
    <header class="chat-header">
      <h1 class="chat-title">树洞 🌿</h1>
      <p class="chat-subtitle">说给一棵树听，它不会告诉任何人</p>
    </header>

    <div class="chat-privacy">
      对话不存历史，刷新即清空 · 若遇危机，请寻求专业帮助
    </div>

    <!-- 消息列表 -->
    <div ref="scrollRef" class="chat-scroll">
      <div class="chat-list">
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="msg-row"
          :class="msg.role === 'user' ? 'msg-row--user' : 'msg-row--ai'"
        >
          <!-- 头像 -->
          <div class="msg-avatar">
            {{ msg.role === 'user' ? '🙂' : '🌿' }}
          </div>
          <!-- 气泡 -->
          <div class="msg-bubble" :class="msg.role === 'user' ? 'msg-bubble--user' : 'msg-bubble--ai'">
            <p class="msg-text">{{ msg.content }}</p>
          </div>
        </div>

        <!-- typing 动效 -->
        <transition name="fade">
          <div v-if="loading" class="msg-row msg-row--ai">
            <div class="msg-avatar">🌿</div>
            <div class="msg-bubble msg-bubble--ai msg-typing">
              <span class="typing-label">正在听</span>
              <span class="typing-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </span>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- 输入区（底部固定） -->
    <div class="chat-input-wrap">
      <div class="chat-input-inner">
        <textarea
          ref="inputRef"
          v-model="input"
          class="chat-input"
          rows="1"
          placeholder="说点什么吧…（Enter 发送，Shift+Enter 换行）"
          @keydown="onKeyDown"
          @input="autoGrow"
        ></textarea>
        <button
          class="chat-send"
          :disabled="!input.trim() || loading"
          @click="send"
        >
          {{ loading ? '…' : '送出' }}
        </button>
      </div>
    </div>

    <!-- toast -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 760px;
  margin: 0 auto;
  padding: 0 16px;
  /* 留给输入区高度 */
  padding-bottom: 0;
  position: relative;
}

/* 顶部 */
.chat-header {
  text-align: center;
  padding: 20px 0 8px;
}
.chat-title {
  font-family: var(--font-serif, serif);
  font-size: 24px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 4px;
  letter-spacing: 0.08em;
}
.chat-subtitle {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
  font-family: var(--font-serif, serif);
  font-style: italic;
}

.chat-privacy {
  text-align: center;
  font-size: 11.5px;
  color: var(--color-text-muted, #8B7B5E);
  opacity: 0.85;
  padding: 4px 8px 12px;
  line-height: 1.6;
}

/* 消息列表 */
.chat-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 4px 4px 20px;
  scroll-behavior: smooth;
}
.chat-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 120px; /* 避开底部输入区 */
}

/* 消息行 */
.msg-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  max-width: 100%;
}
.msg-row--user {
  flex-direction: row-reverse;
}
.msg-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm, 0 2px 8px rgba(139, 123, 94, 0.06));
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
}
.msg-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.7;
  word-break: break-word;
  box-shadow: var(--shadow-sm, 0 2px 8px rgba(139, 123, 94, 0.06));
}
/* AI 气泡：白色卡片 */
.msg-bubble--ai {
  background: rgba(255, 255, 255, 0.85);
  color: var(--color-text-primary, #3D3327);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  border-bottom-left-radius: 6px;
  backdrop-filter: blur(10px);
}
/* 用户气泡：淡绿 → 淡粉 渐变 */
.msg-bubble--user {
  background: linear-gradient(135deg, #DCEBD8 0%, #F5D9D6 100%);
  color: #3D3327;
  border-bottom-right-radius: 6px;
}
.msg-text {
  margin: 0;
  white-space: pre-wrap;
}

/* typing 动效 */
.msg-typing {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
}
.typing-label {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
}
.typing-dots {
  display: inline-flex;
  gap: 4px;
}
.typing-dots .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent, #B8A590);
  animation: dot-bounce 1.2s infinite ease-in-out both;
}
.typing-dots .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dots .dot:nth-child(2) { animation-delay: -0.16s; }
.typing-dots .dot:nth-child(3) { animation-delay: 0s; }
@keyframes dot-bounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  40% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

/* 输入区 */
.chat-input-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
  background: linear-gradient(180deg, rgba(249, 246, 240, 0) 0%, rgba(249, 246, 240, 0.92) 35%, rgba(249, 246, 240, 1) 100%);
  padding: 16px 16px calc(16px + env(safe-area-inset-bottom));
}
.chat-input-inner {
  max-width: 760px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  border-radius: 22px;
  padding: 8px 8px 8px 16px;
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.1));
  backdrop-filter: blur(20px);
}
.chat-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  resize: none;
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text-primary, #3D3327);
  padding: 6px 0;
  max-height: 160px;
  min-height: 24px;
}
.chat-input::placeholder {
  color: var(--color-text-muted, #8B7B5E);
  opacity: 0.7;
}
.chat-send {
  flex-shrink: 0;
  padding: 8px 18px;
  border-radius: 16px;
  background: linear-gradient(135deg, #B8A590 0%, #8B7B5E 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s var(--ease-soft, cubic-bezier(0.22, 1, 0.36, 1));
}
.chat-send:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(139, 123, 94, 0.3);
}
.chat-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* toast */
.toast {
  position: fixed;
  bottom: 96px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(90, 70, 50, 0.92);
  color: #fff;
  padding: 10px 22px;
  border-radius: 20px;
  font-size: 13.5px;
  z-index: 200;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(6px);
  white-space: nowrap;
}
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}

/* typing / loading 行淡入 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s var(--ease-soft, cubic-bezier(0.22, 1, 0.36, 1)), transform 0.3s var(--ease-soft, cubic-bezier(0.22, 1, 0.36, 1));
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* 响应式 */
@media (max-width: 640px) {
  .chat-view {
    padding: 0 12px;
  }
  .chat-title {
    font-size: 21px;
  }
  .msg-bubble {
    max-width: 80%;
    font-size: 14.5px;
  }
  .msg-avatar {
    width: 34px;
    height: 34px;
    font-size: 18px;
  }
  .chat-input-inner {
    padding: 6px 6px 6px 14px;
  }
  .chat-send {
    padding: 7px 14px;
    font-size: 13.5px;
  }
}
</style>
