<script setup>
import { ref } from 'vue'

const props = defineProps({
  code: { type: String, required: true },
})
const emit = defineEmits(['done'])
const copied = ref(false)

async function copyCode() {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1800)
  } catch {
    // 剪贴板不可用时选中文字，让用户手动复制
    const el = document.querySelector('.recovery-code__value')
    if (el) {
      const range = document.createRange()
      range.selectNodeContents(el)
      const sel = window.getSelection()
      sel.removeAllRanges()
      sel.addRange(range)
    }
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="recovery-mask" role="dialog" aria-modal="true" aria-labelledby="recovery-title">
      <div class="recovery-card">
        <div class="recovery-card__icon">🔑</div>
        <h2 id="recovery-title" class="recovery-card__title">请保存你的恢复码</h2>
        <p class="recovery-card__desc">
          忘记密码时，需要昵称 + 这枚恢复码才能重设密码。它只会显示这一次。
        </p>
        <div class="recovery-code">
          <span class="recovery-code__value">{{ code }}</span>
          <button class="recovery-code__copy" type="button" @click="copyCode">
            {{ copied ? '已复制' : '复制' }}
          </button>
        </div>
        <p class="recovery-card__warn">
          ⚠️ 不要发给别人，也不要只存在聊天记录里。建议记在纸上或密码管理器。
        </p>
        <button class="btn btn--primary recovery-card__btn" type="button" @click="emit('done')">
          我已保存，进入静屿
        </button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.recovery-mask {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(74, 68, 56, 0.45);
  backdrop-filter: blur(6px);
}
.recovery-card {
  width: min(430px, 100%);
  padding: 34px 30px 28px;
  border-radius: 24px;
  background: #FFFDF8;
  border: 1px solid #EDE5D8;
  box-shadow: 0 24px 70px rgba(60, 50, 40, .28);
  text-align: center;
}
.recovery-card__icon { font-size: 2.2rem; margin-bottom: 8px; }
.recovery-card__title {
  font-family: var(--font-serif, serif);
  font-size: 1.35rem;
  font-weight: 500;
  color: #5C5348;
  margin: 0 0 10px;
}
.recovery-card__desc {
  color: #8B7B5E;
  font-size: .88rem;
  line-height: 1.75;
  margin: 0 0 18px;
}
.recovery-code {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #F4EFE5;
  border: 1px dashed #D8C9B5;
}
.recovery-code__value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 1.4rem;
  letter-spacing: .18em;
  color: #4A4438;
  user-select: all;
}
.recovery-code__copy {
  border: none;
  border-radius: 999px;
  padding: 6px 12px;
  background: #E8DDCC;
  color: #6B5A48;
  font-size: .78rem;
  cursor: pointer;
}
.recovery-card__warn {
  color: #B08A6A;
  font-size: .76rem;
  line-height: 1.7;
  margin: 16px 0 20px;
}
.recovery-card__btn { width: 100%; }
</style>
