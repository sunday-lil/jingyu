<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const goBack = () => router.back()

// 用户头像是否是图片 URL（vs emoji 文本）
const isUserAvatarImage = computed(() => {
  const a = userStore.avatar
  return !!(a && (a.startsWith('/') || a.startsWith('http')))
})

// 当前对话 ID（后端文件存储用）
const conversationId = ref(null)

// 对话消息（内存中显示）
// 每条结构：{ role: 'user' | 'assistant', content: string }
const messages = ref([
  { role: 'assistant', content: '🌳 我在这里。想说什么都可以，不用整理好情绪再来。' },
])

const input = ref('')
const loading = ref(false)

// 历史对话列表（来自后端文件存储）
const conversations = ref([])
const historyDrawerOpen = ref(false)
const historyLoading = ref(false)

// 结束对话弹窗
const endDialogOpen = ref(false)

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

// 拉取历史对话列表
const fetchConversations = async () => {
  historyLoading.value = true
  try {
    const res = await api.get('/ai/conversations')
    conversations.value = res?.items || []
  } catch (e) {
    // 静默
  } finally {
    historyLoading.value = false
  }
}

// 时间格式化
const formatTime = (str) => {
  if (!str) return ''
  const d = new Date(str)
  if (isNaN(d.getTime())) return str
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${hh}:${mm}`
}

// 开启新对话（如果当前对话已有内容，会被保留在文件中）
const startNewConversation = async () => {
  // 调后端创建新对话
  try {
    const res = await api.post('/ai/conversations')
    conversationId.value = res?.conversation_id || null
  } catch (e) {
    // 静默：后端会在首次 chat 时自动创建
    conversationId.value = null
  }
  messages.value = [
    { role: 'assistant', content: '🌳 新的一段对话开始了。想说什么都可以，我会一直在这里听。' },
  ]
  historyDrawerOpen.value = false
  await scrollToBottom()
}

// 加载历史对话
const loadConversation = async (convId) => {
  if (!convId) return
  try {
    const res = await api.get(`/ai/conversations/${convId}`)
    const msgs = res?.messages || []
    conversationId.value = convId
    if (msgs.length === 0) {
      messages.value = [
        { role: 'assistant', content: '🌳 这段对话还没有开始。' },
      ]
    } else {
      messages.value = msgs.map(m => ({ role: m.role, content: m.content }))
    }
    historyDrawerOpen.value = false
    await scrollToBottom()
  } catch (e) {
    showToast(e.message || '加载历史失败')
  }
}

// 删除历史对话
const deleteConversation = async (convId) => {
  if (!convId) return
  if (!confirm('确定要放下这段对话吗？此操作不可恢复。')) return
  try {
    await api.delete(`/ai/conversations/${convId}`)
    conversations.value = conversations.value.filter(c => c.conversation_id !== convId)
    if (conversationId.value === convId) {
      await startNewConversation()
    }
    showToast('已放下这段对话 🍃')
  } catch (e) {
    showToast(e.message || '删除失败')
  }
}

// 打开"结束对话"弹窗
const openEndDialog = () => {
  // 如果当前对话只有开场白，无需结束
  const realMsgs = messages.value.filter(m => m.role === 'user')
  if (realMsgs.length === 0) {
    showToast('还没有开始对话呢')
    return
  }
  endDialogOpen.value = true
}

// 选择"保留" → 不删除文件，直接开新对话
const endWithKeep = async () => {
  endDialogOpen.value = false
  await startNewConversation()
  showToast('这段对话已保留 🌳')
  fetchConversations()
}

// 选择"不保留" → 删除文件，开新对话
const endWithDiscard = async () => {
  endDialogOpen.value = false
  if (conversationId.value) {
    try {
      await api.delete(`/ai/conversations/${conversationId.value}`)
    } catch (e) {
      // 静默
    }
  }
  await startNewConversation()
  showToast('这段对话已随风而去 🍃')
  fetchConversations()
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

  // 3. 调 AI 端点
  try {
    const res = await api.post('/ai/chat', {
      messages: messages.value
        .filter((m) => m.content) // 过滤空内容
        .map((m) => ({ role: m.role, content: m.content })),
      scene: 'treehole',
      conversation_id: conversationId.value,
      // today_mood / today_diary 由后端自动注入
    })

    // 兼容返回：{ reply, model, available, conversation_id } 或 { data: {...} }
    const data = res && res.data ? res.data : res
    const available = data?.available !== false
    const reply = data?.reply || ''

    // 保存 conversation_id（后端可能新建了对话）
    if (data?.conversation_id) {
      conversationId.value = data.conversation_id
    }

    // v2.4.2：更新落叶余额 + 徽章解锁 toast（对话满 20 次 → 树洞倾心）
    if (typeof data?.leaves_balance === 'number') {
      userStore.updateResources({ leaves: data.leaves_balance })
    }
    let badgeShown = false
    if (Array.isArray(data?.new_badges) && data.new_badges.length > 0) {
      const badgeTexts = data.new_badges.map(b => `${b.image} 解锁徽章「${b.name}」· 赠 ${data.new_leaves} 落叶`)
      showToast(badgeTexts.join('  '), 4000)
      badgeShown = true
    }

    if (!available && !badgeShown) {
      // 降级：AI 不在岛上 —— 但后端已把降级 reply 也写入历史，前端直接展示
      showToast('AI 暂时不在岛上')
    }

    if (reply) {
      messages.value.push({ role: 'assistant', content: reply })
    } else if (available && !badgeShown) {
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
onMounted(async () => {
  // 拉历史对话列表
  fetchConversations()
  // 自动开一段新对话
  await startNewConversation()

  nextTick(() => {
    // 只做位移动画，不设 opacity 初始态（防动画中断后永久不可见）
    gsap.from('.chat-header', { y: -16, duration: 0.6, ease: 'power2.out' })
    gsap.from('.chat-privacy', {
      y: -8,
      duration: 0.6,
      ease: 'power2.out',
      delay: 0.1,
    })
    gsap.from('.msg-row', {
      y: 14,
      duration: 0.5,
      ease: 'power3.out',
      stagger: 0.08,
      delay: 0.15,
    })
    gsap.from('.chat-input-wrap', {
      y: 20,
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
    <!-- 顶部标题 + 操作 -->
    <header class="chat-header">
      <div class="chat-header__left">
        <h1 class="chat-title">🌳 心语树洞</h1>
        <p class="chat-subtitle">说给一棵树听，它不会告诉任何人</p>
      </div>
      <div class="chat-header__actions">
        <button class="chat-action-btn" @click="historyDrawerOpen = true" title="历史对话">
          📜
        </button>
        <button class="chat-action-btn" @click="openEndDialog" title="结束对话">
          🍃
        </button>
      </div>
    </header>

    <div class="chat-privacy">
      树洞会参考你今日的心情与日记，给出针对性的陪伴 · 对话可选择保留或随风去
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
            <img v-if="msg.role === 'user' && isUserAvatarImage" :src="userStore.avatar" class="msg-avatar-img" alt="" />
            <template v-else>{{ msg.role === 'user' ? userStore.avatar : '🌳' }}</template>
          </div>
          <!-- 气泡 -->
          <div class="msg-bubble" :class="msg.role === 'user' ? 'msg-bubble--user' : 'msg-bubble--ai'">
            <p class="msg-text">{{ msg.content }}</p>
          </div>
        </div>

        <!-- typing 动效 -->
        <transition name="fade">
          <div v-if="loading" class="msg-row msg-row--ai">
            <div class="msg-avatar">🌳</div>
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

    <!-- 历史对话抽屉 -->
    <transition name="drawer">
      <div v-if="historyDrawerOpen" class="drawer-mask" @click.self="historyDrawerOpen = false">
        <aside class="drawer">
          <div class="drawer__head">
            <h3 class="drawer__title">📜 历史对话</h3>
            <button class="drawer__close" @click="historyDrawerOpen = false">×</button>
          </div>
          <div class="drawer__body">
            <button class="drawer__new" @click="startNewConversation">
              ＋ 开启新对话
            </button>
            <div v-if="historyLoading" class="drawer__empty">加载中…</div>
            <div v-else-if="conversations.length === 0" class="drawer__empty">
              还没有保留的对话
            </div>
            <ul v-else class="drawer__list">
              <li
                v-for="c in conversations"
                :key="c.conversation_id"
                class="drawer__item"
                :class="{ 'is-active': c.conversation_id === conversationId }"
                @click="loadConversation(c.conversation_id)"
              >
                <div class="drawer__item-preview">
                  {{ c.preview || '（空对话）' }}
                </div>
                <div class="drawer__item-meta">
                  <span>{{ formatTime(c.updated_at || c.created_at) }}</span>
                  <span>· {{ c.message_count }} 条</span>
                  <button
                    class="drawer__item-del"
                    title="放下这段对话"
                    @click.stop="deleteConversation(c.conversation_id)"
                  >×</button>
                </div>
              </li>
            </ul>
          </div>
        </aside>
      </div>
    </transition>

    <!-- 结束对话弹窗：保留 / 不保留 -->
    <transition name="modal">
      <div v-if="endDialogOpen" class="modal-mask" @click.self="endDialogOpen = false">
        <div class="modal-card card">
          <div class="modal-card__icon">🍃</div>
          <h3 class="modal-card__title">结束这段对话？</h3>
          <p class="modal-card__hint">树洞会询问你：是否保留这段对话？</p>
          <div class="modal-actions modal-actions--column">
            <button class="btn btn--primary" @click="endWithKeep">
              🌳 保留 · 留在历史中
            </button>
            <button class="btn btn--ghost" @click="endWithDiscard">
              🍃 不保留 · 随风而去
            </button>
            <button class="btn btn--ghost modal-cancel" @click="endDialogOpen = false">
              继续聊一会儿
            </button>
          </div>
        </div>
      </div>
    </transition>

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
  height: 100dvh;  /* iOS 16+ Safari 底部地址栏出现/消失时视口自动适配 */
  max-width: 760px;
  margin: 0 auto;
  padding: 0 16px;
  /* 留给输入区高度 */
  padding-bottom: 0;
  position: relative;
}

/* 顶部 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 0 8px;
  gap: 12px;
}
.chat-header__left {
  flex: 1;
  min-width: 0;
}
.chat-title {
  font-family: var(--font-serif, serif);
  font-size: 22px;
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
.chat-header__actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.chat-action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  font-size: 16px;
  cursor: pointer;
  transition: all 0.25s var(--ease-soft, ease);
  display: grid;
  place-items: center;
}
.chat-action-btn:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: scale(1.05);
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
  overflow: hidden;
}
.msg-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
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

/* 桌面端：输入框固定在视口底部，避开顶部导航 */
@media (min-width: 1025px) {
  .chat-input-wrap {
    /* 桌面端无底部 tabbar，直接 0 + safe-area 即可 */
    bottom: 0;
  }
}

/* 平板：同桌面 */
@media (min-width: 769px) and (max-width: 1024px) {
  .chat-input-wrap {
    bottom: 0;
  }
}

/* 移动端：输入框需避开底部 tabbar（72px）+ safe-area */
@media (max-width: 768px) {
  .chat-input-wrap {
    /* 上移避开 AppLayout 的 tabbar */
    bottom: calc(72px + env(safe-area-inset-bottom));
    padding-bottom: 12px;
  }
  .chat-list {
    /* 移动端底部留空：输入框 + tabbar */
    padding-bottom: calc(180px + env(safe-area-inset-bottom));
  }
  /* 顶部留空避开 mobile-topbar */
  .chat-header {
    padding-top: calc(20px + env(safe-area-inset-top));
  }
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
  font-family: inherit;
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
  border: none;
  cursor: pointer;
}
.chat-send:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(139, 123, 94, 0.3);
}
.chat-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 历史抽屉 */
.drawer-mask {
  position: fixed;
  inset: 0;
  background: rgba(60, 50, 40, 0.45);
  backdrop-filter: blur(6px);
  z-index: 150;
  display: flex;
  justify-content: flex-end;
}
.drawer {
  width: 320px;
  max-width: 85vw;
  background: var(--color-bg-primary, #F9F6F0);
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: -8px 0 24px rgba(0, 0, 0, 0.1);
}
.drawer__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
}
.drawer__title {
  font-family: var(--font-serif, serif);
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin: 0;
  letter-spacing: 0.05em;
}
.drawer__close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: transparent;
  border: none;
  font-size: 22px;
  color: var(--color-text-muted, #8B7B5E);
  cursor: pointer;
  transition: background 0.2s;
}
.drawer__close:hover {
  background: rgba(139, 123, 94, 0.08);
}
.drawer__body {
  flex: 1;
  overflow-y: auto;
  padding: 14px 16px;
}
.drawer__new {
  width: 100%;
  padding: 12px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(184, 213, 186, 0.3), rgba(232, 246, 233, 0.5));
  border: 1.5px dashed rgba(90, 138, 110, 0.4);
  color: #5A8A6E;
  font-family: var(--font-serif, serif);
  font-size: 14px;
  letter-spacing: 0.05em;
  cursor: pointer;
  margin-bottom: 14px;
  transition: all 0.25s var(--ease-soft, ease);
}
.drawer__new:hover {
  background: linear-gradient(135deg, rgba(184, 213, 186, 0.45), rgba(232, 246, 233, 0.7));
  transform: translateY(-1px);
}
.drawer__empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-text-muted, #8B7B5E);
  font-size: 13px;
}
.drawer__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.drawer__item {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.12));
  cursor: pointer;
  transition: all 0.2s var(--ease-soft, ease);
}
.drawer__item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(-2px);
}
.drawer__item.is-active {
  background: linear-gradient(135deg, rgba(184, 213, 186, 0.25), rgba(255, 255, 255, 0.7));
  border-color: rgba(90, 138, 110, 0.4);
}
.drawer__item-preview {
  font-size: 13px;
  color: var(--color-text-secondary, #5C4F3E);
  line-height: 1.5;
  margin-bottom: 6px;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.drawer__item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
}
.drawer__item-del {
  margin-left: auto;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #8B7B5E);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.drawer__item-del:hover {
  background: rgba(197, 120, 120, 0.15);
  color: #C57878;
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.3s var(--ease-soft);
}
.drawer-enter-active .drawer,
.drawer-leave-active .drawer {
  transition: transform 0.3s var(--ease-soft);
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from .drawer,
.drawer-leave-to .drawer {
  transform: translateX(100%);
}

/* 结束对话弹窗 */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(60, 50, 40, 0.45);
  backdrop-filter: blur(6px);
  display: grid;
  place-items: center;
  z-index: 160;
  padding: 20px;
}
.modal-card {
  max-width: 420px;
  width: 100%;
  padding: 32px 28px;
  text-align: center;
}
.modal-card__icon {
  font-size: 40px;
  margin-bottom: 10px;
}
.modal-card__title {
  font-family: var(--font-serif, serif);
  font-size: 20px;
  font-weight: 500;
  margin: 0 0 6px;
  color: var(--color-text-primary, #3D3327);
}
.modal-card__hint {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0 0 20px;
  line-height: 1.6;
}
.modal-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}
.modal-actions--column {
  flex-direction: column;
}
.modal-actions--column .btn {
  width: 100%;
}
.modal-cancel {
  margin-top: 6px;
  font-size: 13px;
  opacity: 0.7;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s var(--ease-soft);
}
.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition: transform 0.3s var(--ease-soft), opacity 0.3s var(--ease-soft);
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-card,
.modal-leave-to .modal-card {
  transform: translateY(12px) scale(0.98);
  opacity: 0;
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
  max-width: 80%;
  text-align: center;
  line-height: 1.5;
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

/* 响应式：移动端紧凑样式 */
@media (max-width: 768px) {
  .chat-view {
    padding: 0 12px;
  }
  .chat-title {
    font-size: 19px;
  }
  .chat-subtitle {
    font-size: 12px;
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
  .chat-action-btn {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
  .drawer {
    width: 280px;
  }
}
</style>
