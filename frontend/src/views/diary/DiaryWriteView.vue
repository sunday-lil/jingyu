<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 日记内容（明文）
const content = ref('')
const submitting = ref(false)

// 发布选项：默认放入漂流瓶（公开可见）
// - bottle: 放入漂流瓶（公开可见，允许评论）
// - secret: 不放入漂流瓶（仅自己可见，自动同步至树洞）
const publishChoice = ref('bottle')

// 简易 toast
const toastVisible = ref(false)
const toastText = ref('')
let toastTimer = null
const showToast = (text, duration = 2200) => {
  toastText.value = text
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, duration)
}

// 提交日记（明文，无密码加密）
const handleSubmit = async () => {
  if (!content.value.trim()) {
    showToast('写点什么再让它漂出去吧')
    return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    const isPublic = publishChoice.value === 'bottle'
    const sendToAi = publishChoice.value === 'secret'
    const res = await api.post('/diary', {
      content: content.value.trim(),
      is_public: isPublic,
      send_to_ai_hole: sendToAi,
    })
    // 后端返回 { id, created_at, granted_energy, new_total_energy, new_leaves, leaves_balance, new_badges }
    if (typeof res?.new_total_energy === 'number') {
      userStore.updateEnergy(res.new_total_energy)
    }
    // v2.4.2：更新落叶余额
    if (typeof res?.leaves_balance === 'number') {
      userStore.updateResources({ leaves: res.leaves_balance })
    }
    // v2.4.2：徽章解锁 toast（写满 30 篇 → 日记达人）
    if (Array.isArray(res?.new_badges) && res.new_badges.length > 0) {
      const badgeTexts = res.new_badges.map(b => `${b.image} 解锁徽章「${b.name}」· 赠 ${res.new_leaves} 落叶`)
      showToast(badgeTexts.join('  '))
    } else {
      showToast(isPublic ? '日记已放入海中 🌊' : '日记已悄悄收好，并说给树洞听了 🌳')
    }
    setTimeout(() => {
      router.push('/diary')
    }, 700)
  } catch (e) {
    showToast(e.message || '提交失败，请稍后再试')
  } finally {
    submitting.value = false
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
</script>

<template>
  <div class="diary-write-view">
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

    <header class="write-header">
      <button class="back-btn" @click="router.push('/diary')">← 回海岸</button>
      <h1 class="write-title">写一篇日记</h1>
      <p class="write-verse">"写下心事，让它随浪花漂去远方"</p>
    </header>

    <div class="write-form card">
      <!-- 日记内容（明文，无 emoji 选择，无密码加密） -->
      <div class="form-group">
        <label class="form-label">日记内容</label>
        <textarea
          v-model="content"
          class="form-input content-area"
          placeholder="此刻心里在想什么…"
          rows="10"
        ></textarea>
        <div class="content-hint">日记将以明文保存，可随时回看</div>
      </div>

      <!-- 发布选项 -->
      <div class="form-group">
        <label class="form-label">放归何处</label>
        <div class="publish-options">
          <label
            class="publish-option"
            :class="{ 'is-active': publishChoice === 'bottle' }"
          >
            <input
              type="radio"
              v-model="publishChoice"
              value="bottle"
              class="publish-option__radio"
            >
            <span class="publish-option__icon">🏺</span>
            <span class="publish-option__body">
              <span class="publish-option__title">放入漂流瓶</span>
              <span class="publish-option__desc">公开可见 · 陌生人可拾取并留鼓励</span>
            </span>
          </label>
          <label
            class="publish-option"
            :class="{ 'is-active': publishChoice === 'secret' }"
          >
            <input
              type="radio"
              v-model="publishChoice"
              value="secret"
              class="publish-option__radio"
            >
            <span class="publish-option__icon">🌳</span>
            <span class="publish-option__body">
              <span class="publish-option__title">不放入漂流瓶</span>
              <span class="publish-option__desc">仅自己可见 · 自动同步至树洞</span>
            </span>
          </label>
        </div>
      </div>

      <!-- 提交 -->
      <button class="btn btn--primary submit-btn" :disabled="submitting" @click="handleSubmit">
        {{ submitting ? '正在送出…' : (publishChoice === 'bottle' ? '🌊 放入海中' : '🌳 悄悄收好') }}
      </button>
    </div>

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
.write-header,
.write-form,
.toast {
  position: relative;
  z-index: 1;
}

/* 平板紧凑 */
@media (min-width: 769px) and (max-width: 1024px) {
  .diary-write-view {
    padding: 28px 20px 72px;
  }
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
  background: transparent;
  border: none;
  cursor: pointer;
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

.content-area {
  resize: vertical;
  min-height: 220px;
  line-height: 1.8;
  font-size: 15px;
}
.content-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
}

/* 发布选项 */
.publish-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.publish-option {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.6);
  border: 1.5px solid var(--color-border, rgba(139, 123, 94, 0.15));
  border-radius: var(--radius-md, 14px);
  cursor: pointer;
  transition: all 0.25s var(--ease-soft, ease);
}
.publish-option:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}
.publish-option.is-active {
  background: linear-gradient(135deg, rgba(184, 165, 144, 0.18), rgba(255, 255, 255, 0.7));
  border-color: var(--color-accent, #B8A590);
  box-shadow: 0 4px 14px rgba(184, 165, 144, 0.22);
}
.publish-option__radio {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.publish-option__icon {
  font-size: 28px;
  line-height: 1;
  flex-shrink: 0;
}
.publish-option__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.publish-option__title {
  font-family: var(--font-serif, serif);
  font-size: 15px;
  color: var(--color-text-primary, #3D3327);
  letter-spacing: 0.05em;
}
.publish-option__desc {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.03em;
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
  .diary-write-view {
    padding: 20px 14px 60px;
  }
  .write-title {
    font-size: 24px;
  }
  .write-form {
    padding: 20px 16px;
  }
  .content-area {
    min-height: 240px;
    font-size: 15px;
  }
  .publish-option {
    padding: 12px 14px;
    gap: 10px;
  }
  .publish-option__icon {
    font-size: 24px;
  }
  /* toast 上移避开 tabbar */
  .toast {
    bottom: calc(90px + env(safe-area-inset-bottom));
  }
}
</style>
