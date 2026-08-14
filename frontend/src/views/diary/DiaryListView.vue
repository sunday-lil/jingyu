<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'

const router = useRouter()

// 日期格式化
const formatDate = (str) => {
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

// 日记列表（后端返回 { total, page, per_page, items: [...] }）
const diaries = ref([])
const total = ref(0)
const loading = ref(false)
const errorMsg = ref('')

// 拉取日记列表（明文）
const fetchDiaries = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get('/diary/mine', { params: { page: 1, per_page: 50 } })
    diaries.value = res?.items || []
    total.value = res?.total || 0
  } catch (e) {
    errorMsg.value = e.message || '日记加载失败'
  } finally {
    loading.value = false
  }
}

// 详情弹窗（明文，无需解密）
const detailModal = ref({
  visible: false,
  diary: null,
  loading: false,
  encouragements: [],
})

const openDetail = async (d) => {
  detailModal.value = {
    visible: true,
    diary: d,
    loading: true,
    encouragements: [],
  }
  // 拉取详情（含鼓励语列表）
  try {
    const res = await api.get(`/diary/${d.id}`)
    detailModal.value.diary = {
      ...d,
      content: res?.content ?? d.content,
      encouragements: res?.encouragements || [],
    }
    detailModal.value.encouragements = res?.encouragements || []
  } catch (e) {
    // 静默
  } finally {
    detailModal.value.loading = false
  }
}

const closeDetail = () => {
  detailModal.value.visible = false
}

// 删除日记
const deleteDiary = async (id) => {
  if (!confirm('确定要把这篇日记放回海里吗？此操作不可恢复。')) return
  try {
    await api.delete(`/diary/${id}`)
    diaries.value = diaries.value.filter(d => d.id !== id)
    total.value = Math.max(0, total.value - 1)
    closeDetail()
  } catch (e) {
    alert(e.message || '删除失败')
  }
}

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

// 跳转
const goWrite = () => router.push('/diary/write')
const goPick = () => router.push('/diary/pick')

onMounted(() => {
  fetchDiaries()
  nextTick(() => {
    gsap.from('.diary-header', { y: -20, opacity: 0, duration: 0.6, ease: 'power2.out' })
    gsap.from('.diary-item', {
      y: 24,
      opacity: 0,
      duration: 0.7,
      stagger: 0.1,
      ease: 'power3.out',
    })
  })
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="diary-list-view">
    <!-- 大海动效背景（SVG 波浪 + CSS 动画） -->
    <div class="sea-bg" aria-hidden="true">
      <svg class="sea-bg__wave sea-bg__wave--1" viewBox="0 0 1440 200" preserveAspectRatio="none">
        <path d="M0,100 C240,160 480,40 720,100 C960,160 1200,40 1440,100 L1440,200 L0,200 Z" fill="rgba(168, 197, 232, 0.18)"/>
      </svg>
      <svg class="sea-bg__wave sea-bg__wave--2" viewBox="0 0 1440 200" preserveAspectRatio="none">
        <path d="M0,120 C240,60 480,180 720,120 C960,60 1200,180 1440,120 L1440,200 L0,200 Z" fill="rgba(197, 213, 232, 0.22)"/>
      </svg>
      <svg class="sea-bg__wave sea-bg__wave--3" viewBox="0 0 1440 200" preserveAspectRatio="none">
        <path d="M0,140 C240,100 480,170 720,140 C960,100 1200,170 1440,140 L1440,200 L0,200 Z" fill="rgba(232, 240, 246, 0.32)"/>
      </svg>
    </div>

    <!-- 顶部操作区 -->
    <header class="diary-header">
      <div class="diary-header__inner">
        <div class="diary-header__title-wrap">
          <h1 class="diary-header__title">日记海岸</h1>
          <p class="diary-header__verse">"每一篇日记，都是被海风温柔保存的回声"</p>
        </div>
        <div class="diary-header__actions">
          <button class="btn btn--ghost" @click="goPick">🏺 拾瓶</button>
          <button class="btn btn--primary" @click="goWrite">✍️ 写日记</button>
        </div>
      </div>
    </header>

    <!-- 日记时间线（明文） -->
    <section class="timeline">
      <div v-if="loading" class="timeline__empty">日记加载中…</div>
      <div v-else-if="errorMsg" class="timeline__empty">{{ errorMsg }}</div>
      <div v-else-if="diaries.length === 0" class="timeline__empty">
        <div class="empty-emoji">🌊</div>
        <p>海岸上还没有日记，写一篇让它漂出去吧</p>
      </div>
      <ul v-else class="timeline__list">
        <li
          v-for="d in diaries"
          :key="d.id"
          class="diary-item"
          @click="openDetail(d)"
        >
          <div class="diary-item__dot" :class="{ 'diary-item__dot--bottle': d.is_public, 'diary-item__dot--secret': !d.is_public }">
            {{ d.is_public ? '🏺' : '🌳' }}
          </div>
          <div class="diary-item__body">
            <div class="diary-item__date">{{ formatDate(d.created_at) }}</div>
            <div class="diary-item__preview">{{ (d.content || '').slice(0, 60) }}{{ (d.content || '').length > 60 ? '…' : '' }}</div>
            <div class="diary-item__meta">
              <span class="diary-item__tag" :class="d.is_public ? 'diary-item__tag--bottle' : 'diary-item__tag--secret'">
                {{ d.is_public ? '漂流瓶' : '树洞' }}
              </span>
              <span v-if="d.encouragement_count > 0" class="diary-item__encouragements">
                收到 {{ d.encouragement_count }} 句鼓励 💛
              </span>
            </div>
          </div>
          <div class="diary-item__arrow">→</div>
        </li>
      </ul>
    </section>

    <!-- 详情弹窗（明文，无需解密） -->
    <transition name="modal">
      <div v-if="detailModal.visible" class="modal-mask" @click.self="closeDetail">
        <div class="modal-card card">
          <div v-if="detailModal.loading" class="modal-loading">日记加载中…</div>
          <template v-else-if="detailModal.diary">
            <div class="modal-card__head">
              <div class="modal-card__icon">{{ detailModal.diary.is_public ? '🏺' : '🌳' }}</div>
              <div>
                <div class="modal-card__date">{{ formatDate(detailModal.diary.created_at) }}</div>
                <div class="modal-card__tag" :class="detailModal.diary.is_public ? 'modal-card__tag--bottle' : 'modal-card__tag--secret'">
                  {{ detailModal.diary.is_public ? '放入漂流瓶 · 公开可见' : '不放入漂流瓶 · 同步树洞' }}
                </div>
              </div>
            </div>
            <p class="modal-card__content">{{ detailModal.diary.content }}</p>
            <div v-if="detailModal.encouragements.length" class="modal-encouragements">
              <div class="modal-encouragements__title">来自陌生人的鼓励 💛 × {{ detailModal.encouragements.length }}</div>
              <div
                v-for="(e, i) in detailModal.encouragements"
                :key="i"
                class="modal-encouragements__item"
              >
                {{ typeof e === 'string' ? e : (e.content || e.text || '') }}
              </div>
            </div>
            <div class="modal-actions">
              <button class="btn btn--ghost modal-delete" @click="deleteDiary(detailModal.diary.id)">放回海里</button>
              <button class="btn btn--primary" @click="closeDetail">合上日记</button>
            </div>
          </template>
        </div>
      </div>
    </transition>

    <!-- toast 轻提示 -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.diary-list-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px 80px;
  position: relative;
}

/* 大海动效背景 */
.sea-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}
.sea-bg__wave {
  position: absolute;
  left: 0;
  right: 0;
  width: 200%;
  height: 220px;
  bottom: 0;
}
.sea-bg__wave--1 {
  animation: wave-slide 18s linear infinite;
  opacity: 0.7;
}
.sea-bg__wave--2 {
  animation: wave-slide 26s linear infinite reverse;
  opacity: 0.6;
  bottom: -10px;
}
.sea-bg__wave--3 {
  animation: wave-slide 32s linear infinite;
  opacity: 0.8;
  bottom: -20px;
}
@keyframes wave-slide {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

/* 内容上浮到 z=1 */
.diary-header,
.timeline,
.modal-mask,
.toast {
  position: relative;
  z-index: 1;
}

/* 平板紧凑 */
@media (min-width: 769px) and (max-width: 1024px) {
  .diary-list-view {
    padding: 28px 20px 72px;
  }
}

/* 顶部 */
.diary-header {
  margin-bottom: 36px;
}
.diary-header__inner {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  flex-wrap: wrap;
}
.diary-header__title {
  font-family: var(--font-serif, serif);
  font-size: 30px;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
  font-weight: 500;
  letter-spacing: 0.1em;
}
.diary-header__verse {
  font-family: var(--font-serif, serif);
  font-style: italic;
  font-size: 14px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
}
.diary-header__actions {
  display: flex;
  gap: 10px;
}

/* 时间线 */
.timeline__empty {
  text-align: center;
  padding: 80px 20px;
  color: var(--color-text-secondary, #5C4F3E);
  font-size: 14px;
}
.empty-emoji {
  font-size: 48px;
  margin-bottom: 12px;
  display: inline-block;
  animation: float 4s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.timeline__list {
  list-style: none;
  margin: 0;
  padding: 0;
  position: relative;
}
.timeline__list::before {
  content: '';
  position: absolute;
  left: 33px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: linear-gradient(to bottom, transparent, var(--color-border, rgba(139, 123, 94, 0.15)), transparent);
}
.diary-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px 16px 12px;
  margin-bottom: 12px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  border-radius: var(--radius-lg, 20px);
  cursor: pointer;
  transition: transform 0.25s var(--ease-soft), box-shadow 0.25s var(--ease-soft), background 0.25s;
}
.diary-item:hover {
  transform: translateX(4px);
  background: rgba(255, 255, 255, 0.85);
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.1));
}
.diary-item__dot {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
  z-index: 1;
  box-shadow: 0 0 0 4px var(--color-bg-primary, #F9F6F0);
}
.diary-item__dot--bottle {
  background: linear-gradient(135deg, rgba(168, 197, 232, 0.35), rgba(232, 240, 246, 0.5));
}
.diary-item__dot--secret {
  background: linear-gradient(135deg, rgba(184, 213, 186, 0.35), rgba(232, 246, 233, 0.5));
}
.diary-item__body {
  flex: 1;
  min-width: 0;
}
.diary-item__date {
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}
.diary-item__preview {
  font-size: 14px;
  color: var(--color-text-secondary, #5C4F3E);
  line-height: 1.5;
  word-break: break-word;
}
.diary-item__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
  flex-wrap: wrap;
}
.diary-item__tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  letter-spacing: 0.05em;
}
.diary-item__tag--bottle {
  background: rgba(168, 197, 232, 0.25);
  color: #5A7A9E;
}
.diary-item__tag--secret {
  background: rgba(184, 213, 186, 0.25);
  color: #5A8A6E;
}
.diary-item__encouragements {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
}
.diary-item__arrow {
  color: var(--color-text-muted, #8B7B5E);
  font-size: 16px;
  flex-shrink: 0;
}

/* 弹窗 */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(60, 50, 40, 0.45);
  backdrop-filter: blur(6px);
  display: grid;
  place-items: center;
  z-index: 100;
  padding: 20px;
}
.modal-card {
  max-width: 520px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
  padding: 28px 26px;
}
.modal-loading {
  text-align: center;
  padding: 24px;
  color: var(--color-text-muted, #8B7B5E);
  font-size: 14px;
}
.modal-card__head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}
.modal-card__icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--color-bg-primary, #F9F6F0);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  flex-shrink: 0;
}
.modal-card__date {
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  margin-bottom: 4px;
  letter-spacing: 0.05em;
}
.modal-card__tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  display: inline-block;
}
.modal-card__tag--bottle {
  background: rgba(168, 197, 232, 0.25);
  color: #5A7A9E;
}
.modal-card__tag--secret {
  background: rgba(184, 213, 186, 0.25);
  color: #5A8A6E;
}
.modal-card__content {
  text-align: left;
  font-size: 15px;
  line-height: 1.9;
  color: var(--color-text-primary, #3D3327);
  background: rgba(249, 246, 240, 0.6);
  padding: 16px 18px;
  border-radius: var(--radius-md, 14px);
  margin: 0 0 20px;
  white-space: pre-wrap;
  word-break: break-word;
}
.modal-encouragements {
  margin: 0 0 20px;
  text-align: left;
}
.modal-encouragements__title {
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--color-text-secondary, #5C4F3E);
  margin-bottom: 10px;
}
.modal-encouragements__item {
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-text-secondary, #5C4F3E);
  background: rgba(255, 255, 255, 0.5);
  border-radius: var(--radius-sm, 8px);
  padding: 8px 12px;
  margin-bottom: 6px;
}
.modal-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 8px;
}
.modal-delete {
  color: #C57878;
  border-color: rgba(197, 120, 120, 0.3);
}
.modal-delete:hover {
  background: rgba(197, 120, 120, 0.08);
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
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(90, 70, 50, 0.9);
  color: #fff;
  padding: 10px 22px;
  border-radius: 20px;
  font-size: 14px;
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
  transform: translateX(-50%) translateY(10px);
}

/* ── 移动端（≤768px）：差异化布局 ── */
@media (max-width: 768px) {
  .diary-list-view {
    padding: 20px 14px 60px;
  }
  .diary-header__title {
    font-size: 24px;
  }
  .diary-header__inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }
  .diary-header__actions {
    width: 100%;
  }
  .diary-header__actions .btn {
    flex: 1;
  }
  /* 时间线左移，dot 缩小 */
  .timeline__list::before {
    left: 21px;
  }
  .diary-item {
    gap: 12px;
    padding: 14px 16px 14px 10px;
  }
  .diary-item__dot {
    width: 36px;
    height: 36px;
    font-size: 18px;
    box-shadow: 0 0 0 3px var(--color-bg-primary, #F9F6F0);
  }
  .diary-item__date {
    font-size: 12px;
  }
  .diary-item__preview {
    font-size: 13px;
  }
  /* toast 上移避开 tabbar */
  .toast {
    bottom: calc(90px + env(safe-area-inset-bottom));
  }
  /* 弹窗在小屏底部留空 */
  .modal-card {
    max-width: calc(100vw - 32px);
    padding: 22px 18px;
  }
  .modal-actions {
    flex-direction: column;
  }
  .modal-actions .btn {
    width: 100%;
  }
}
</style>
