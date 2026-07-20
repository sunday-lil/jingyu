<script setup>
/**
 * SceneHint — 3D 场景交互指引横幅
 *
 * 解决问题：旧版用户不知道怎么和 3D 场景交互，只有一行静态小字
 *
 * 行为：
 * - 进入场景 800ms 后渐入
 * - 默认 5s 后自动消失
 * - 用户首次与场景交互（pointerdown / wheel / touchstart）立即消失
 * - 支持父组件通过 v-model:visible 双向控制
 *
 * 视觉：
 * - 毛玻璃 + 圆角胶囊
 * - 左侧手势图标 + 右侧提示文字
 * - 配 prefers-reduced-motion 关闭动效
 */
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  // 提示文字（必填）
  text: { type: String, required: true },
  // 手势/图标类型，影响左侧 glyph
  // drag-rotate | scroll-zoom | click | drag-rotate-zoom | touch
  gesture: {
    type: String,
    default: 'drag-rotate-zoom',
    validator: (v) =>
      ['drag-rotate', 'scroll-zoom', 'click', 'drag-rotate-zoom', 'touch'].includes(v),
  },
  // 自动消失延迟（ms），0 表示不自动消失
  autoHide: { type: Number, default: 5000 },
  // 出现延迟（ms）
  showDelay: { type: Number, default: 800 },
  // 显隐双向绑定（可选）
  visible: { type: Boolean, default: null },
})

const emit = defineEmits(['update:visible', 'dismiss'])

const internalVisible = ref(false)
let autoHideTimer = null
let showDelayTimer = null
let interactionBound = false

// 图标库（SVG path）
const ICONS = {
  'drag-rotate': 'M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41',
  'scroll-zoom': 'M12 4v16M7 9l5-5 5 5M7 15l5 5 5-5',
  click: 'M12 2a10 10 0 100 20 10 10 0 000-20zM12 8v8M8 12h8',
  'drag-rotate-zoom':
    'M3 12a9 9 0 1018 0 9 9 0 00-18 0zM12 7v10M7 12h10M9 9l-2 2 2 2M15 9l2 2-2 2',
  touch: 'M9 11V6a2 2 0 114 0v5M9 11V8a2 2 0 014 0v3M9 11V7a2 2 0 014 0v4M9 11V9a2 2 0 014 0v2a4 4 0 01-4 4H8a3 3 0 01-3-3v-1',
}

const iconPath = ICONS[props.gesture] || ICONS['drag-rotate-zoom']

const show = () => {
  if (props.visible === false) return
  internalVisible.value = true
  emit('update:visible', true)
  bindInteraction()
  if (props.autoHide > 0) {
    autoHideTimer = setTimeout(hide, props.autoHide)
  }
}

const hide = () => {
  internalVisible.value = false
  emit('update:visible', false)
  emit('dismiss')
  unbindInteraction()
  if (autoHideTimer) {
    clearTimeout(autoHideTimer)
    autoHideTimer = null
  }
}

// 监听全局用户首次交互，立即消失
const onFirstInteraction = () => {
  if (internalVisible.value) hide()
}

const bindInteraction = () => {
  if (interactionBound) return
  window.addEventListener('pointerdown', onFirstInteraction, { passive: true, once: true })
  window.addEventListener('wheel', onFirstInteraction, { passive: true, once: true })
  window.addEventListener('touchstart', onFirstInteraction, { passive: true, once: true })
  interactionBound = true
}

const unbindInteraction = () => {
  if (!interactionBound) return
  window.removeEventListener('pointerdown', onFirstInteraction)
  window.removeEventListener('wheel', onFirstInteraction)
  window.removeEventListener('touchstart', onFirstInteraction)
  interactionBound = false
}

// 外部 v-model:visible 控制
watch(
  () => props.visible,
  (v) => {
    if (v === true && !internalVisible.value) show()
    else if (v === false && internalVisible.value) hide()
  },
)

onMounted(() => {
  showDelayTimer = setTimeout(show, props.showDelay)
})

onBeforeUnmount(() => {
  if (showDelayTimer) clearTimeout(showDelayTimer)
  if (autoHideTimer) clearTimeout(autoHideTimer)
  unbindInteraction()
})
</script>

<template>
  <transition name="hint-fade">
    <div v-if="internalVisible" class="scene-hint" role="status" aria-live="polite">
      <svg
        class="scene-hint__icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path :d="iconPath" />
      </svg>
      <span class="scene-hint__text">{{ text }}</span>
    </div>
  </transition>
</template>

<style scoped>
.scene-hint {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 999px;
  box-shadow: 0 8px 32px rgba(74, 68, 56, 0.12),
              inset 0 1px 0 rgba(255, 255, 255, 0.8);
  color: var(--color-text-primary, #3D3327);
  font-family: var(--font-serif, serif);
  font-size: 13px;
  letter-spacing: 0.06em;
  pointer-events: none;
  z-index: 5;
  white-space: nowrap;
  user-select: none;
}

.scene-hint__icon {
  width: 18px;
  height: 18px;
  color: var(--color-accent-dark, #8B7B5E);
  flex-shrink: 0;
  animation: hint-icon-pulse 2.4s ease-in-out infinite;
}

.scene-hint__text {
  line-height: 1.4;
}

@keyframes hint-icon-pulse {
  0%, 100% { transform: scale(1); opacity: 0.85; }
  50% { transform: scale(1.15); opacity: 1; }
}

/* 入场动效 */
.hint-fade-enter-active,
.hint-fade-leave-active {
  transition: opacity 0.6s var(--ease-apple, cubic-bezier(0.16, 1, 0.3, 1)),
              transform 0.6s var(--ease-apple, cubic-bezier(0.16, 1, 0.3, 1));
}
.hint-fade-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}
.hint-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-4px);
}

@media (max-width: 640px) {
  .scene-hint {
    bottom: 16px;
    padding: 8px 16px;
    font-size: 12px;
    gap: 8px;
  }
  .scene-hint__icon {
    width: 16px;
    height: 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .scene-hint__icon {
    animation: none;
  }
  .hint-fade-enter-active,
  .hint-fade-leave-active {
    transition: opacity 0.2s linear;
  }
  .hint-fade-enter-from,
  .hint-fade-leave-to {
    transform: translateX(-50%);
  }
}
</style>
