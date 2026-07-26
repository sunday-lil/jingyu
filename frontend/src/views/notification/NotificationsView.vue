<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'

const router = useRouter()

// 数据
const notifications = ref([])
const loading = ref(false)
const errorMsg = ref('')

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
  }, 2000)
}

// 通知类型映射
const TYPE_INFO = {
  encouragement: { icon: '💛', label: '鼓励', color: '#F5C875' },
  system:        { icon: '🔔', label: '系统', color: '#A8C5E8' },
}

const typeInfo = (t) => TYPE_INFO[t] || { icon: '🔔', label: '通知', color: '#B8A590' }

// 时间格式化（相对时间 + 绝对时间）
const formatTime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const diff = Date.now() - d.getTime()
  const min = Math.floor(diff / 60_000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} 小时前`
  const day = Math.floor(hr / 24)
  if (day < 7) return `${day} 天前`
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day2 = String(d.getDate()).padStart(2, '0')
  return `${m}-${day2}`
}

const formatDateFull = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${hh}:${mm}`
}

// 统计
const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)
const hasUnread = computed(() => unreadCount.value > 0)

// 拉取通知
const fetchNotifications = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get('/notifications')
    notifications.value = res?.items || []
    await nextTick()
    if (document.querySelector('.notif-item')) {
      gsap.from('.notif-item', {
        y: 16, opacity: 0, duration: 0.45, stagger: 0.05, ease: 'power2.out',
      })
    }
  } catch (e) {
    errorMsg.value = e.message || '通知加载失败'
  } finally {
    loading.value = false
  }
}

// 点击单条通知 → 标记已读 + 跳转
const handleNotifClick = async (n) => {
  if (!n.is_read) {
    try {
      await api.post(`/notifications/${n.id}/read`)
      n.is_read = true
    } catch {
      // 静默
    }
  }
  // 鼓励语通知跳到日记海岸（related_id 是 diary_id）
  if (n.type === 'encouragement' && n.related_id) {
    router.push('/diary')
  }
}

// 全部已读
const markingAll = ref(false)
const markAllRead = async () => {
  if (markingAll.value || !hasUnread.value) return
  markingAll.value = true
  try {
    await api.post('/notifications/read-all')
    notifications.value.forEach(n => { n.is_read = true })
    showToast('已全部标记为已读')
  } catch (e) {
    showToast(e.message || '操作失败')
  } finally {
    markingAll.value = false
  }
}

const goBack = () => {
  if (window.history.length > 1) router.back()
  else router.push('/profile')
}

onMounted(() => {
  fetchNotifications()
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="notif-view">
    <!-- 顶部 -->
    <header class="notif-header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <h1 class="notif-title">通知</h1>
      <p class="notif-verse">"海风送来的回响"</p>
      <div class="notif-header__bar" v-if="notifications.length">
        <span class="notif-header__count">
          共 {{ notifications.length }} 条
          <span v-if="hasUnread" class="notif-header__unread">· 未读 {{ unreadCount }}</span>
        </span>
        <button
          class="btn btn--ghost notif-header__read-all"
          :disabled="markingAll || !hasUnread"
          @click="markAllRead"
        >
          {{ markingAll ? '处理中…' : '全部已读' }}
        </button>
      </div>
    </header>

    <!-- 加载/空状态 -->
    <div v-if="loading && !notifications.length" class="empty-state card">
      正在倾听海风的回响…
    </div>
    <div v-else-if="errorMsg" class="empty-state card">{{ errorMsg }}</div>
    <div v-else-if="!notifications.length" class="empty-state card">
      <div class="empty-emoji">🌙</div>
      <p>这里很安静，还没有通知</p>
      <p class="empty-hint">当你的漂流瓶收到鼓励时，会在这里提醒你</p>
    </div>

    <!-- 通知列表 -->
    <ul v-else class="notif-list">
      <li
        v-for="n in notifications"
        :key="n.id"
        class="notif-item"
        :class="{ 'is-unread': !n.is_read }"
        @click="handleNotifClick(n)"
      >
        <div class="notif-item__icon" :style="{ background: typeInfo(n.type).color + '33' }">
          {{ typeInfo(n.type).icon }}
        </div>
        <div class="notif-item__body">
          <div class="notif-item__content">{{ n.content }}</div>
          <div class="notif-item__meta">
            <span class="notif-item__type">{{ typeInfo(n.type).label }}</span>
            <span class="notif-item__dot">·</span>
            <span class="notif-item__time" :title="formatDateFull(n.created_at)">{{ formatTime(n.created_at) }}</span>
            <span v-if="!n.is_read" class="notif-item__unread-dot"></span>
          </div>
        </div>
        <div class="notif-item__arrow" v-if="n.type === 'encouragement'">→</div>
      </li>
    </ul>

    <!-- toast -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.notif-view {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* 平板紧凑 */
@media (min-width: 769px) and (max-width: 1024px) {
  .notif-view {
    padding: 28px 20px 72px;
  }
}

/* 顶部 */
.notif-header {
  margin-bottom: 24px;
}
.back-btn {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  margin-bottom: 14px;
  padding: 0;
  transition: color 0.2s;
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: inherit;
}
.back-btn:hover {
  color: var(--color-accent-dark, #8B7B5E);
}
.notif-title {
  font-family: var(--font-serif, serif);
  font-size: 28px;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
  font-weight: 500;
  letter-spacing: 0.1em;
}
.notif-verse {
  font-family: var(--font-serif, serif);
  font-style: italic;
  font-size: 14px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0 0 16px;
}
.notif-header__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: rgba(255, 255, 255, 0.55);
  border-radius: var(--radius-md, 14px);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
}
.notif-header__count {
  font-size: 13px;
  color: var(--color-text-secondary, #5C4F3E);
}
.notif-header__unread {
  color: #C5946B;
  font-weight: 500;
}
.notif-header__read-all {
  padding: 5px 12px;
  font-size: 12px;
}
.notif-header__read-all:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-muted, #8B7B5E);
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.empty-emoji {
  font-size: 48px;
  margin-bottom: 8px;
}
.empty-hint {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
}

/* 列表 */
.notif-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(8px);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  border-radius: var(--radius-lg, 20px);
  cursor: pointer;
  transition: transform 0.25s var(--ease-soft, ease), background 0.25s, box-shadow 0.25s;
}
.notif-item:hover {
  transform: translateX(2px);
  background: rgba(255, 255, 255, 0.85);
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.1));
}
.notif-item.is-unread {
  background: linear-gradient(135deg, rgba(255, 248, 220, 0.6) 0%, rgba(255, 255, 255, 0.7) 100%);
  border-color: rgba(245, 200, 117, 0.3);
}
.notif-item__icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.notif-item__body {
  flex: 1;
  min-width: 0;
}
.notif-item__content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 6px;
  word-break: break-word;
}
.notif-item__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  flex-wrap: wrap;
}
.notif-item__type {
  padding: 1px 8px;
  background: rgba(184, 165, 144, 0.15);
  border-radius: 8px;
  letter-spacing: 0.05em;
}
.notif-item__dot {
  opacity: 0.5;
}
.notif-item__unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #E89A9A;
  margin-left: 4px;
}
.notif-item__arrow {
  color: var(--color-text-muted, #8B7B5E);
  font-size: 16px;
  flex-shrink: 0;
  align-self: center;
}

/* toast */
.toast {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(90, 70, 50, 0.92);
  color: #fff;
  padding: 12px 22px;
  border-radius: 22px;
  font-size: 14px;
  z-index: 200;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
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
  transform: translateX(-50%) translateY(10px);
}

/* 移动端 */
@media (max-width: 768px) {
  .notif-view {
    padding: 20px 14px 80px;
  }
  .notif-title {
    font-size: 24px;
  }
  .notif-item {
    padding: 14px 16px;
    gap: 12px;
  }
  .notif-item__icon {
    width: 34px;
    height: 34px;
    font-size: 17px;
  }
  .notif-item__content {
    font-size: 13.5px;
  }
  /* toast 上移避开 tabbar */
  .toast {
    bottom: calc(90px + env(safe-area-inset-bottom));
  }
}
</style>
