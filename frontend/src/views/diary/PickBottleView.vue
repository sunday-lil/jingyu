<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'

const router = useRouter()

// 心情 emoji 映射
const MOOD_EMOJI = {
  happy: '😊',
  smile: '😀',
  neutral: '😐',
  sad: '😢',
  cry: '😭',
}
const MOOD_LABEL = {
  happy: '开心',
  smile: '不错',
  neutral: '平静',
  sad: '难过',
  cry: '崩溃',
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
const bottle = ref(null) // 当前拾到的日记
const picking = ref(false)
const errorMsg = ref('')

// 已解密的明文
const plainText = ref('')

// 解密弹窗
const passwordModal = ref({
  visible: false,
  password: '',
  error: '',
  loading: false,
})

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

// 拾一个漂流瓶
const pickBottle = async () => {
  picking.value = true
  errorMsg.value = ''
  bottle.value = null
  plainText.value = ''
  aiEncouragement.value = ''
  encourageText.value = ''
  try {
    const res = await api.get('/diary/pick/random')
    // 兼容两种返回：直接对象/null 或 { data: {...} }
    const data = res && (res.id !== undefined ? res : res?.data)
    if (!data) {
      errorMsg.value = '海面上暂时没有漂流瓶了，过一会儿再来吧'
      picking.value = false
      return
    }
    bottle.value = data
    picking.value = false
    // 弹密码框
    passwordModal.value = {
      visible: true,
      password: '',
      error: '',
      loading: false,
    }
  } catch (e) {
    errorMsg.value = e.message || '拾瓶失败'
    picking.value = false
  }
}

// 解密当前瓶子
const doDecrypt = async () => {
  if (!bottle.value) return
  const pwd = passwordModal.value.password
  if (!pwd) {
    passwordModal.value.error = '请输入密码'
    return
  }
  passwordModal.value.loading = true
  passwordModal.value.error = ''
  try {
    // 用当前用户密码 + 日记所有者的 salt 解密
    const plain = await decryptText(bottle.value.content_encrypted, pwd, bottle.value.salt)
    if (plain === null) {
      passwordModal.value.error = '解密失败，密码可能不对'
    } else {
      plainText.value = plain
      passwordModal.value.visible = false
      // 如果瓶子里没有鼓励语，自动拉 AI 鼓励
      if (!bottle.value.encouragements || bottle.value.encouragements.length === 0) {
        fetchAiEncouragement(plain)
      }
    }
  } catch {
    passwordModal.value.error = '解密出错'
  } finally {
    passwordModal.value.loading = false
  }
}

const closePasswordModal = () => {
  if (passwordModal.value.loading) return
  passwordModal.value.visible = false
  // 还没解密成功就放弃，把瓶子放回海里
  if (!plainText.value) {
    bottle.value = null
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
    // 兼容多种返回形状：字符串 / { encouragement } / { data: {...} } / { data: '...' }
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

// 写一句鼓励
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

// ── 加密辅助函数（Web Crypto API） ──
async function deriveKey(password, saltBase64) {
  const enc = new TextEncoder()
  const keyMaterial = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey'])
  const salt = Uint8Array.from(atob(saltBase64), c => c.charCodeAt(0))
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: 200000, hash: 'SHA-256' },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  )
}
async function decryptText(cipherBase64, password, saltBase64) {
  try {
    const key = await deriveKey(password, saltBase64)
    const combined = Uint8Array.from(atob(cipherBase64), c => c.charCodeAt(0))
    const iv = combined.slice(0, 12)
    const cipher = combined.slice(12)
    const plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, cipher)
    return new TextDecoder().decode(plain)
  } catch { return null }
}
</script>

<template>
  <div class="pick-bottle-view">
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

    <!-- 日记展示 -->
    <section v-else class="bottle-section">
      <div class="bottle-card card">
        <div class="bottle-card__head">
          <div class="bottle-card__emoji">{{ moodEmoji(bottle.mood_type) }}</div>
          <div class="bottle-card__meta">
            <div class="bottle-card__mood">{{ moodLabel(bottle.mood_type) }}</div>
            <div class="bottle-card__date">{{ formatDate(bottle.created_at) }}</div>
          </div>
        </div>
        <p class="bottle-card__content">{{ plainText }}</p>
      </div>

      <!-- 已有鼓励语 -->
      <div v-if="bottle.encouragements && bottle.encouragements.length" class="encouragement-list">
        <h3 class="encouragement-list__title">来自陌生人的鼓励 💛</h3>
        <div
          v-for="(e, i) in bottle.encouragements"
          :key="i"
          class="encouragement-item"
        >
          {{ typeof e === 'string' ? e : (e.content || e.text || '') }}
        </div>
      </div>

      <!-- AI 鼓励语（瓶子无鼓励语时自动拉取） -->
      <div v-else class="ai-encouragement">
        <h3 class="ai-encouragement__title">AI 想对你说 🌿</h3>
        <div v-if="aiLoading" class="ai-encouragement__loading">正在为这篇日记寻一句温柔…</div>
        <p v-else-if="aiEncouragement" class="ai-encouragement__text">{{ aiEncouragement }}</p>
      </div>

      <!-- 写一句鼓励 -->
      <div class="encourage-form">
        <label class="form-label">给写日记的人一句鼓励</label>
        <div class="encourage-form__row">
          <input
            v-model="encourageText"
            class="form-input encourage-form__input"
            type="text"
            placeholder="一句温柔的话…"
            :disabled="encourageSubmitting"
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

    <!-- 密码弹窗 -->
    <transition name="modal">
      <div v-if="passwordModal.visible" class="modal-mask" @click.self="closePasswordModal">
        <div class="modal-card card">
          <div class="modal-card__icon">🔑</div>
          <h3 class="modal-card__title">输入密码解开瓶子</h3>
          <p class="modal-card__hint">用你的密码尝试解开这只瓶子</p>
          <input
            v-model="passwordModal.password"
            type="password"
            class="form-input modal-input"
            placeholder="至少 6 位"
            autocomplete="current-password"
            @keyup.enter="doDecrypt"
          >
          <div v-if="passwordModal.error" class="modal-error">{{ passwordModal.error }}</div>
          <div class="modal-actions">
            <button class="btn btn--ghost" @click="closePasswordModal">放弃</button>
            <button class="btn btn--primary" :disabled="passwordModal.loading" @click="doDecrypt">
              {{ passwordModal.loading ? '解锁中…' : '解锁' }}
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
.pick-bottle-view {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px 80px;
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
.encouragement-item {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  border-radius: var(--radius-md, 14px);
  padding: 14px 18px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 8px;
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
  max-width: 460px;
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
  margin: 0 0 18px;
  line-height: 1.6;
}
.modal-input {
  margin-bottom: 12px;
  text-align: left;
}
.modal-error {
  color: #C57878;
  font-size: 13px;
  margin: 6px 0 12px;
}
.modal-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
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
  white-space: nowrap;
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

@media (max-width: 640px) {
  .pick-bottle-view {
    padding: 20px 16px 60px;
  }
  .pick-hero {
    padding: 40px 22px;
  }
  .pick-hero__emoji {
    font-size: 52px;
  }
  .bottle-card {
    padding: 22px 18px;
  }
  .encourage-form__row {
    flex-direction: column;
  }
  .encourage-form__btn {
    padding: 12px;
  }
}
</style>
