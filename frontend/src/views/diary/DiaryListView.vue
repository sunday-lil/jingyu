<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'

const router = useRouter()

// 心情 emoji 映射（后端 mood_type → emoji）
const MOOD_EMOJI = {
  happy: '😊',
  smile: '😀',
  neutral: '😐',
  sad: '😢',
  cry: '😭',
}
const moodEmoji = (t) => MOOD_EMOJI[t] || '🍃'

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

// 日记列表
const diaries = ref([])
const loading = ref(false)
const errorMsg = ref('')

// 拉取日记列表
const fetchDiaries = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get('/diary/list')
    // 兼容两种返回：直接数组 或 { data: [...] }
    diaries.value = Array.isArray(res)
      ? res
      : (Array.isArray(res?.data) ? res.data : [])
  } catch (e) {
    errorMsg.value = e.message || '日记加载失败'
  } finally {
    loading.value = false
  }
}

// 解密弹窗
const decryptModal = ref({
  visible: false,
  diary: null,
  password: '',
  plainText: '',
  decrypting: false,
  error: '',
})

const openDecrypt = (diary) => {
  decryptModal.value = {
    visible: true,
    diary,
    password: '',
    plainText: '',
    decrypting: false,
    error: '',
  }
}

const closeDecrypt = () => {
  if (decryptModal.value.decrypting) return
  decryptModal.value.visible = false
}

// 执行解密
const doDecrypt = async () => {
  const { diary, password } = decryptModal.value
  if (!password) {
    decryptModal.value.error = '请输入密码'
    return
  }
  decryptModal.value.decrypting = true
  decryptModal.value.error = ''
  try {
    const plain = await decryptText(diary.content_encrypted, password, diary.salt)
    if (plain === null) {
      decryptModal.value.error = '解密失败，密码可能不对'
    } else {
      decryptModal.value.plainText = plain
    }
  } catch {
    decryptModal.value.error = '解密出错'
  } finally {
    decryptModal.value.decrypting = false
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
  <div class="diary-list-view">
    <!-- 顶部操作区 -->
    <header class="diary-header">
      <div class="diary-header__inner">
        <div class="diary-header__title-wrap">
          <h1 class="diary-header__title">日记海岸</h1>
          <p class="diary-header__verse">"每一篇日记，都是被海风温柔保存的回声"</p>
        </div>
        <div class="diary-header__actions">
          <button class="btn btn--ghost" @click="goPick">🍶 拾瓶</button>
          <button class="btn btn--primary" @click="goWrite">✍️ 写日记</button>
        </div>
      </div>
    </header>

    <!-- 日记时间线 -->
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
          @click="openDecrypt(d)"
        >
          <div class="diary-item__dot">{{ moodEmoji(d.mood_type) }}</div>
          <div class="diary-item__body">
            <div class="diary-item__date">{{ formatDate(d.created_at) }}</div>
            <div class="diary-item__preview">🔒 加密的日记</div>
            <div v-if="d.encouragements && d.encouragements.length" class="diary-item__encouragements">
              收到 {{ d.encouragements.length }} 句鼓励 💛
            </div>
          </div>
          <div class="diary-item__arrow">→</div>
        </li>
      </ul>
    </section>

    <!-- 解密弹窗 -->
    <transition name="modal">
      <div v-if="decryptModal.visible" class="modal-mask" @click.self="closeDecrypt">
        <div class="modal-card card">
          <!-- 未解密：密码输入 -->
          <div v-if="!decryptModal.plainText">
            <div class="modal-card__icon">🔑</div>
            <h3 class="modal-card__title">输入密码解锁日记</h3>
            <p class="modal-card__hint">用你写日记时的密码解开</p>
            <input
              v-model="decryptModal.password"
              type="password"
              class="form-input modal-input"
              placeholder="至少 6 位"
              autocomplete="current-password"
              @keyup.enter="doDecrypt"
            >
            <div v-if="decryptModal.error" class="modal-error">{{ decryptModal.error }}</div>
            <div class="modal-actions">
              <button class="btn btn--ghost" @click="closeDecrypt">取消</button>
              <button class="btn btn--primary" :disabled="decryptModal.decrypting" @click="doDecrypt">
                {{ decryptModal.decrypting ? '解锁中…' : '解锁' }}
              </button>
            </div>
          </div>
          <!-- 已解密：显示内容 -->
          <div v-else>
            <div class="modal-card__icon">{{ moodEmoji(decryptModal.diary.mood_type) }}</div>
            <div class="modal-card__date">{{ formatDate(decryptModal.diary.created_at) }}</div>
            <p class="modal-card__content">{{ decryptModal.plainText }}</p>
            <div v-if="decryptModal.diary.encouragements && decryptModal.diary.encouragements.length" class="modal-encouragements">
              <div class="modal-encouragements__title">来自陌生人的鼓励 💛</div>
              <div
                v-for="(e, i) in decryptModal.diary.encouragements"
                :key="i"
                class="modal-encouragements__item"
              >
                {{ typeof e === 'string' ? e : (e.content || e.text || '') }}
              </div>
            </div>
            <div class="modal-actions">
              <button class="btn btn--primary" @click="closeDecrypt">合上日记</button>
            </div>
          </div>
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
  background: var(--color-bg-primary, #F9F6F0);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
  z-index: 1;
  box-shadow: 0 0 0 4px var(--color-bg-primary, #F9F6F0);
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
}
.diary-item__encouragements {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  margin-top: 6px;
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
  max-width: 460px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
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
}
.modal-card__date {
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  margin-bottom: 14px;
  letter-spacing: 0.05em;
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
  margin-top: 8px;
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
  .diary-list-view {
    padding: 20px 16px 60px;
  }
  .diary-header__title {
    font-size: 24px;
  }
  .diary-header__inner {
    flex-direction: column;
    align-items: flex-start;
  }
  .diary-header__actions {
    width: 100%;
  }
  .diary-header__actions .btn {
    flex: 1;
  }
}
</style>
