<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'

const router = useRouter()

// 心情选项（5 种 + 不选 null）
const MOOD_OPTIONS = [
  { value: 'happy', emoji: '😊', label: '开心' },
  { value: 'smile', emoji: '😀', label: '不错' },
  { value: 'neutral', emoji: '😐', label: '平静' },
  { value: 'sad', emoji: '😢', label: '难过' },
  { value: 'cry', emoji: '😭', label: '崩溃' },
]

const selectedMood = ref(null) // null = 不选心情
const content = ref('')
const submitting = ref(false) // 保留状态位以备扩展（当前未使用）

// 密码弹窗
const passwordModal = ref({
  visible: false,
  password: '',
  error: '',
  loading: false,
})

const selectMood = (val) => {
  // 再次点击同一种心情 → 取消选择
  selectedMood.value = selectedMood.value === val ? null : val
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
  }, 2200)
}

// 提交：先校验内容 → 弹密码框
const handleSubmit = () => {
  if (!content.value.trim()) {
    showToast('写点什么再让它漂出去吧')
    return
  }
  passwordModal.value = {
    visible: true,
    password: '',
    error: '',
    loading: false,
  }
}

const closePasswordModal = () => {
  if (passwordModal.value.loading) return
  passwordModal.value.visible = false
}

// 真正提交：生成 salt → 加密 → POST
const doSubmit = async () => {
  const pwd = passwordModal.value.password
  if (!pwd || pwd.length < 6) {
    passwordModal.value.error = '密码至少 6 位'
    return
  }
  passwordModal.value.loading = true
  passwordModal.value.error = ''
  try {
    // 1. 生成新 salt
    const salt = generateSalt()
    // 2. 用密码 + salt 加密内容
    const cipher = await encryptText(content.value, pwd, salt)
    // 3. 提交后端（密码不传后端）
    await api.post('/diary/create', {
      content_encrypted: cipher,
      salt,
      mood_type: selectedMood.value,
    })
    showToast('日记已放入海中 🌊')
    setTimeout(() => {
      router.push('/diary')
    }, 600)
  } catch (e) {
    passwordModal.value.error = e.message || '提交失败，请稍后再试'
  } finally {
    passwordModal.value.loading = false
  }
}

onMounted(() => {
  nextTick(() => {
    gsap.from('.write-header', { y: -20, opacity: 0, duration: 0.6, ease: 'power2.out' })
    gsap.from('.write-form > *', {
      y: 20,
      opacity: 0,
      duration: 0.6,
      stagger: 0.1,
      ease: 'power3.out',
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
async function encryptText(text, password, saltBase64) {
  const key = await deriveKey(password, saltBase64)
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const enc = new TextEncoder()
  const cipher = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, enc.encode(text))
  const combined = new Uint8Array(iv.length + cipher.byteLength)
  combined.set(iv, 0)
  combined.set(new Uint8Array(cipher), iv.length)
  return btoa(String.fromCharCode(...combined))
}
function generateSalt() {
  const arr = crypto.getRandomValues(new Uint8Array(16))
  return btoa(String.fromCharCode(...arr))
}
</script>

<template>
  <div class="diary-write-view">
    <header class="write-header">
      <button class="back-btn" @click="router.push('/diary')">← 回海岸</button>
      <h1 class="write-title">写一篇日记</h1>
      <p class="write-verse">"写下心事，让它随浪花漂去远方"</p>
    </header>

    <div class="write-form card">
      <!-- 心情选择 -->
      <div class="form-group">
        <label class="form-label">今天的心情</label>
        <div class="mood-row">
          <button
            v-for="m in MOOD_OPTIONS"
            :key="m.value"
            type="button"
            class="mood-chip"
            :class="{ 'is-active': selectedMood === m.value }"
            @click="selectMood(m.value)"
          >
            <span class="mood-chip__emoji">{{ m.emoji }}</span>
            <span class="mood-chip__label">{{ m.label }}</span>
          </button>
        </div>
      </div>

      <!-- 日记内容 -->
      <div class="form-group">
        <label class="form-label">日记内容</label>
        <textarea
          v-model="content"
          class="form-input content-area"
          placeholder="此刻心里在想什么…"
          rows="8"
        ></textarea>
        <div class="content-hint">内容会被加密后再放入海中，只有持有密码的人能读到</div>
      </div>

      <!-- 提交 -->
      <button class="btn btn--primary submit-btn" :disabled="submitting" @click="handleSubmit">
        🌊 放入海中
      </button>
    </div>

    <!-- 密码弹窗 -->
    <transition name="modal">
      <div v-if="passwordModal.visible" class="modal-mask" @click.self="closePasswordModal">
        <div class="modal-card card">
          <div class="modal-card__icon">🔐</div>
          <h3 class="modal-card__title">设置加密密码</h3>
          <p class="modal-card__hint">密码只在本机用于加密，不会发送到服务器</p>
          <input
            v-model="passwordModal.password"
            type="password"
            class="form-input modal-input"
            placeholder="至少 6 位"
            autocomplete="new-password"
            @keyup.enter="doSubmit"
          >
          <div v-if="passwordModal.error" class="modal-error">{{ passwordModal.error }}</div>
          <div class="modal-actions">
            <button class="btn btn--ghost" @click="closePasswordModal">取消</button>
            <button class="btn btn--primary" :disabled="passwordModal.loading" @click="doSubmit">
              {{ passwordModal.loading ? '正在加密…' : '确认加密' }}
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
.diary-write-view {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

.write-header {
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
.write-title {
  font-family: var(--font-serif, serif);
  font-size: 28px;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
  font-weight: 500;
  letter-spacing: 0.1em;
}
.write-verse {
  font-family: var(--font-serif, serif);
  font-style: italic;
  font-size: 14px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
}

.write-form {
  padding: 32px 28px;
}

.form-group {
  margin-bottom: 24px;
}
.form-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-secondary, #5C4F3E);
  margin-bottom: 10px;
  letter-spacing: 0.05em;
}

.mood-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.mood-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  border-radius: var(--radius-md, 14px);
  transition: all 0.25s var(--ease-soft);
  min-width: 64px;
}
.mood-chip:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}
.mood-chip.is-active {
  background: linear-gradient(135deg, rgba(184, 165, 144, 0.3), rgba(255, 255, 255, 0.6));
  border-color: var(--color-accent, #B8A590);
  box-shadow: 0 4px 14px rgba(184, 165, 144, 0.25);
}
.mood-chip__emoji {
  font-size: 24px;
  line-height: 1;
}
.mood-chip__label {
  font-size: 12px;
  color: var(--color-text-secondary, #5C4F3E);
}

.content-area {
  resize: vertical;
  min-height: 180px;
  line-height: 1.8;
  font-size: 15px;
}
.content-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
}

.submit-btn {
  width: 100%;
  padding: 14px;
  font-size: 15px;
}
.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  .diary-write-view {
    padding: 20px 16px 60px;
  }
  .write-form {
    padding: 22px 18px;
  }
  .mood-chip {
    min-width: 56px;
    padding: 10px 12px;
  }
  .mood-chip__emoji {
    font-size: 20px;
  }
}
</style>
