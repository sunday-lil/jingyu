<script setup>
/**
 * SceneControls — 3D 场景视角控制工具栏
 *
 * 解决问题：旧版只能鼠标被动跟随，无法重置视角 / 切换自动旋转
 *
 * 功能：
 * - 自动旋转开关（默认开，闲置时缓慢自转）
 * - 重置视角按钮（平滑动画回到初始相机位置）
 * - 全屏切换（可选，通过 enableFullscreen prop 开启）
 *
 * 父组件通过 v-model 接管 autoRotate 状态，
 * 通过 @reset 事件接收重置信号（父组件控制相机动画），
 * 通过 @fullscreen 接收全屏切换信号。
 */
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: true }, // autoRotate
  enableFullscreen: { type: Boolean, default: false },
  // 控件位置
  position: {
    type: String,
    default: 'bottom-right',
    validator: (v) =>
      ['top-left', 'top-right', 'bottom-left', 'bottom-right'].includes(v),
  },
})

const emit = defineEmits(['update:modelValue', 'reset', 'fullscreen'])

const isFullscreen = ref(false)

const toggleAutoRotate = () => {
  emit('update:modelValue', !props.modelValue)
}

const onReset = () => {
  emit('reset')
}

const onToggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.().then(() => {
      isFullscreen.value = true
      emit('fullscreen', true)
    }).catch(() => {})
  } else {
    document.exitFullscreen?.().then(() => {
      isFullscreen.value = false
      emit('fullscreen', false)
    }).catch(() => {})
  }
}

const positionClass = computed(() => `scene-controls--${props.position}`)
</script>

<template>
  <div :class="['scene-controls', positionClass]" role="toolbar" aria-label="场景视角控制">
    <button
      type="button"
      class="ctrl-btn"
      :class="{ 'is-active': modelValue }"
      :aria-pressed="modelValue"
      :title="modelValue ? '暂停自动旋转' : '开启自动旋转'"
      @click="toggleAutoRotate"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path v-if="modelValue" d="M6 4h4v16H6zM14 4h4v16h-4z" />
        <path v-else d="M8 5v14l11-7z" />
      </svg>
    </button>

    <button
      type="button"
      class="ctrl-btn"
      title="重置视角"
      aria-label="重置视角"
      @click="onReset"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M3 12a9 9 0 1 0 3-6.7" />
        <path d="M3 4v5h5" />
      </svg>
    </button>

    <button
      v-if="enableFullscreen"
      type="button"
      class="ctrl-btn"
      :title="isFullscreen ? '退出全屏' : '进入全屏'"
      :aria-label="isFullscreen ? '退出全屏' : '进入全屏'"
      @click="onToggleFullscreen"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path v-if="!isFullscreen" d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" />
        <path v-else d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.scene-controls {
  position: absolute;
  display: flex;
  gap: 6px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 14px;
  box-shadow: 0 6px 24px rgba(74, 68, 56, 0.1),
              inset 0 1px 0 rgba(255, 255, 255, 0.7);
  z-index: 5;
}

.scene-controls--top-left { top: 16px; left: 16px; }
.scene-controls--top-right { top: 16px; right: 16px; }
.scene-controls--bottom-left { bottom: 16px; left: 16px; }
.scene-controls--bottom-right { bottom: 16px; right: 16px; }

.ctrl-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--color-text-secondary, #5C4F3E);
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, transform 0.15s ease;
}

.ctrl-btn:hover {
  background: rgba(255, 255, 255, 0.7);
  color: var(--color-text-primary, #3D3327);
  transform: translateY(-1px);
}

.ctrl-btn:active {
  transform: translateY(0);
}

.ctrl-btn.is-active {
  background: linear-gradient(135deg, rgba(184, 165, 144, 0.3), rgba(139, 123, 94, 0.2));
  color: var(--color-accent-dark, #8B7B5E);
}

.ctrl-btn svg {
  width: 18px;
  height: 18px;
}

@media (max-width: 640px) {
  .scene-controls {
    padding: 4px;
    gap: 4px;
  }
  .scene-controls--top-left,
  .scene-controls--top-right { top: 12px; }
  .scene-controls--bottom-left,
  .scene-controls--bottom-right { bottom: 12px; }
  .scene-controls--top-left,
  .scene-controls--bottom-left { left: 12px; }
  .scene-controls--top-right,
  .scene-controls--bottom-right { right: 12px; }
  .ctrl-btn {
    width: 32px;
    height: 32px;
  }
  .ctrl-btn svg {
    width: 16px;
    height: 16px;
  }
}
</style>
