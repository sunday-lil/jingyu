<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'

const router = useRouter()

// 心情 emoji 映射（与后端 MOOD_INFO 对齐 —— v2.3 七种心情）
const MOOD_EMOJI = {
  ecstatic: '🤩',
  happy:    '😊',
  calm:     '😌',
  tired:    '😪',
  anxious:  '😰',
  angry:    '😠',
  sad:      '😢',
}
const MOOD_LABEL = {
  ecstatic: '极度开心',
  happy:    '开心',
  calm:     '平静',
  tired:    '疲惫',
  anxious:  '焦虑',
  angry:    '生气',
  sad:      '悲伤',
}
const moodEmoji = (t) => MOOD_EMOJI[t] || '🍃'
const moodLabel = (t) => MOOD_LABEL[t] || '未知'

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

// 拾瓶状态
const bottle = ref(null) // 当前拾到的日记（明文）
const picking = ref(false)
const errorMsg = ref('')

// AI 鼓励语（瓶子无鼓励语时自动拉取）
const aiEncouragement = ref('')
const aiLoading = ref(false)

// 用户写鼓励的输入
const encourageText = ref('')
const encourageSubmitting = ref(false)

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
  }, 2200)
}

// 拾一个漂流瓶（明文直接返回，无需解密）
const pickBottle = async () => {
  picking.value = true
  errorMsg.value = ''
  bottle.value = null
  aiEncouragement.value = ''
  encourageText.value = ''
  try {
    const res = await api.get('/diary/pick/random')
    // 后端返回明文 content 的对象，或 404
    const data = res && (res.id !== undefined ? res : res?.data)
    if (!data) {
      errorMsg.value = '海面上暂时没有漂流瓶了，过一会儿再来吧'
      picking.value = false
      return
    }
    bottle.value = data
    picking.value = false
    // 如果瓶子里没有鼓励语，自动拉 AI 鼓励
    if (!data.encouragement_count) {
      fetchAiEncouragement(data.content)
    }
  } catch (e) {
    errorMsg.value = e.message || '拾瓶失败'
    picking.value = false
  }
}

// 拉 AI 鼓励语（瓶子无鼓励语时）
const fetchAiEncouragement = async (fullText) => {
  if (!bottle.value) return
  aiLoading.value = true
  try {
    const preview = (fullText || '').slice(0, 120)
    const res = await api.post('/ai/encouragement', {
      diary_preview: preview,
      mood_label: moodLabel(bottle.value.mood_type),
    })
    // 兼容多种返回形状
    let text = ''
    if (typeof res === 'string') text = res
    else if (typeof res?.data === 'string') text = res.data
    else text =
      res?.encouragement ||
      res?.data?.encouragement ||
      res?.text ||
      res?.data?.text ||
      res?.message ||
      res?.data?.message ||
      ''
    aiEncouragement.value = text || '愿这片海浪带走你的疲惫。'
  } catch {
    aiEncouragement.value = ''
  } finally {
    aiLoading.value = false
  }
}

// 写一句鼓励（评论返回发布者 + 消息提醒）
const sendEncourage = async () => {
  if (!bottle.value) return
  const text = encourageText.value.trim()
  if (!text) {
    showToast('写一句鼓励再送出吧')
    return
  }
  encourageSubmitting.value = true
  try {
    await api.post(`/diary/${bottle.value.id}/encourage`, { content: text })
    showToast('你的鼓励已被海风带走 💛')
    encourageText.value = ''
    // 鼓励数 +1
    bottle.value = {
      ...bottle.value,
      encouragement_count: (bottle.value.encouragement_count || 0) + 1,
    }
  } catch (e) {
    showToast(e.message || '发送失败')
  } finally {
    encourageSubmitting.value = false
  }
}

onMounted(() => {
  nextTick(() => {
    gsap.from('.pick-header', { y: -20, opacity: 0, duration: 0.6, ease: 'power2.out' })
    gsap.from('.pick-hero', {
      y: 20,
      opacity: 0,
      duration: 0.8,
      ease: 'power3.out',
      delay: 0.1,
    })
  })
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="pick-bottle-view">
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

    <header class="pick-header">
      <button class="back-btn" @click="router.push('/diary')">← 回海岸</button>
      <h1 class="pick-title">拾一个漂流瓶</h1>
      <p class="pick-verse">"海浪送来陌生人的一句心事"</p>
    </header>

    <!-- 拾瓶入口 -->
    <section v-if="!bottle" class="pick-hero card">
      <div class="pick-hero__emoji">🍶</div>
      <p class="pick-hero__text">点击下方按钮，从海里拾起一只漂流瓶</p>
      <button class="btn btn--primary pick-hero__btn" :disabled="picking" @click="pickBottle">
        {{ picking ? '正在拾起…' : '🌊 拾一个' }}
      </button>
      <div v-if="errorMsg" class="pick-hero__error">{{ errorMsg }}</div>
    </section>

    <!-- 日记展示（明文，无需解密） -->
    <section v-else class="bottle-section">
      <div class="bottle-card card">
        <div class="bottle-card__head">
          <div class="bottle-card__emoji">{{ moodEmoji(bottle.mood_type) }}</div>
          <div class="bottle-card__meta">
            <div class="bottle-card__mood">{{ moodLabel(bottle.mood_type) }}</div>
            <div class="bottle-card__date">{{ formatDate(bottle.created_at) }}</div>
          </div>
        </div>
        <p class="bottle-card__content">{{ bottle.content }}</p>
      </div>

      <!-- 已有鼓励语 -->
      <div v-if="bottle.encouragement_count > 0" class="encouragement-list">
        <h3 class="encouragement-list__title">来自陌生人的鼓励 💛 × {{ bottle.encouragement_count }}</h3>
        <p class="encouragement-list__hint">在「我的日记」详情页可以看到全部鼓励</p>
      </div>

      <!-- AI 鼓励语（瓶子无鼓励语时自动拉取） -->
      <div v-else class="ai-encouragement">
        <h3 class="ai-encouragement__title">AI 想对你说 🌿</h3>
        <div v-if="aiLoading" class="ai-encouragement__loading">正在为这篇日记寻一句温柔…</div>
        <p v-else-if="aiEncouragement" class="ai-encouragement__text">{{ aiEncouragement }}</p>
      </div>

      <!-- 写一句鼓励（评论返回发布者 + 消息提醒） -->
      <div class="encourage-form">
        <label class="form-label">给写日记的人一句鼓励</label>
        <div class="encourage-form__row">
          <input
            v-model="encourageText"
            class="form-input encourage-form__input"
            type="text"
            placeholder="一句温柔的话…"
            :disabled="encourageSubmitting"
            maxlength="200"
          >
          <button
            class="btn btn--primary encourage-form__btn"
            :disabled="encourageSubmitting"
            @click="sendEncourage"
          >
            {{ encourageSubmitting ? '送出中…' : '送出' }}
          </button>
        </div>
      </div>

      <!-- 再拾一个 -->
      <div class="pick-again">
        <button class="btn btn--ghost" :disabled="picking" @click="pickBottle">
          🌊 再拾一个
        </button>
      </div>
    </section>

    <!-- toast -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.pick-bottle-view {
  max-width: 720px;
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
.pick-header,
.pick-hero,
.bottle-section,
.toast {
  position: relative;
  z-index: 1;
}

/* 平板紧凑 */
@media (min-width: 769px) and (max-width: 1024px) {
  .pick-bottle-view {
    padding: 28px 20px 72px;
  }
}

.pick-header {
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
}
.back-btn:hover {
  color: var(--color-accent-dark, #8B7B5E);
}
.pick-title {
  font-family: var(--font-serif, serif);
  font-size: 28px;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
  font-weight: 500;
  letter-spacing: 0.1em;
}
.pick-verse {
  font-family: var(--font-serif, serif);
  font-style: italic;
  font-size: 14px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
}

/* hero */
.pick-hero {
  text-align: center;
  padding: 60px 32px;
}
.pick-hero__emoji {
  font-size: 64px;
  margin-bottom: 18px;
  display: inline-block;
  animation: float 4s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.pick-hero__text {
  color: var(--color-text-secondary, #5C4F3E);
  font-size: 14px;
  margin: 0 0 24px;
}
.pick-hero__btn {
  padding: 12px 28px;
  font-size: 15px;
}
.pick-hero__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.pick-hero__error {
  margin-top: 18px;
  font-size: 13px;
  color: #C57878;
}

/* bottle */
.bottle-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.bottle-card {
  padding: 28px 26px;
}
.bottle-card__head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}
.bottle-card__emoji {
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
.bottle-card__mood {
  font-family: var(--font-serif, serif);
  font-size: 16px;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 2px;
}
.bottle-card__date {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
}
.bottle-card__content {
  font-size: 15px;
  line-height: 1.9;
  color: var(--color-text-primary, #3D3327);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  background: rgba(249, 246, 240, 0.6);
  padding: 18px 20px;
  border-radius: var(--radius-md, 14px);
}

/* 鼓励语列表 */
.encouragement-list__title,
.ai-encouragement__title {
  font-family: var(--font-serif, serif);
  font-size: 16px;
  color: var(--color-text-secondary, #5C4F3E);
  margin: 0 0 12px;
  font-weight: 500;
}
.encouragement-list__hint {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
}

/* AI 鼓励 */
.ai-encouragement__loading {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: var(--radius-md, 14px);
}
.ai-encouragement__text {
  font-family: var(--font-serif, serif);
  font-style: italic;
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-text-primary, #3D3327);
  background: linear-gradient(135deg, rgba(184, 165, 144, 0.15), rgba(255, 255, 255, 0.6));
  padding: 18px 20px;
  border-radius: var(--radius-md, 14px);
  border: 1px solid rgba(184, 165, 144, 0.2);
  margin: 0;
}

/* 鼓励输入 */
.encourage-form__row {
  display: flex;
  gap: 10px;
}
.encourage-form__input {
  flex: 1;
}
.encourage-form__btn {
  white-space: nowrap;
}
.encourage-form__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.form-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-secondary, #5C4F3E);
  margin-bottom: 10px;
  letter-spacing: 0.05em;
}

.pick-again {
  text-align: center;
  margin-top: 8px;
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
  .pick-bottle-view {
    padding: 20px 14px 60px;
  }
  .pick-title {
    font-size: 24px;
  }
  .pick-hero {
    padding: 40px 18px;
  }
  .pick-hero__emoji {
    font-size: 52px;
  }
  .bottle-card {
    padding: 20px 16px;
  }
  .bottle-card__head {
    gap: 12px;
    margin-bottom: 14px;
  }
  .bottle-card__emoji {
    width: 44px;
    height: 44px;
    font-size: 22px;
  }
  .bottle-card__content {
    padding: 14px 16px;
    font-size: 14.5px;
  }
  .encourage-form__row {
    flex-direction: column;
  }
  .encourage-form__btn {
    padding: 12px;
    width: 100%;
  }
  /* toast 上移避开 tabbar */
  .toast {
    bottom: calc(90px + env(safe-area-inset-bottom));
  }
}
</style>
