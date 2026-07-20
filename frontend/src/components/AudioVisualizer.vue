<script setup>
/**
 * AudioVisualizer.vue — 5 色音波可视化
 *
 * 集成位置：MusicDetailView 顶部 detail-header 之下，曲目列表之上
 *
 * 实现：
 *   - Web Audio API 的 AnalyserNode 读取 <audio> 实时频谱
 *   - Canvas2D 绘制 5 条流动的曲线（对应宫商角徵羽 5 音色）
 *   - 每条曲线用对应五音色 + 透明度叠加，形成柔和波形
 *
 * 渐进降级：
 *   - 不支持 Web Audio API → 显示静态 5 色横条（CSS）
 *   - reduced-motion → 显示静态波形插画
 *   - 未播放 → 显示极低振幅"待机"波纹
 *
 * 性能：
 *   - 30fps 渲染（移动端 24fps）
 *   - smartRAF 标签页隐藏自动暂停
 *   - fftSize = 256（够用，CPU 友好）
 */
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { shouldUseCanvas, isMobile, smartRAF } from '@/utils/visual'

const props = defineProps({
  // 当前五音 key（用于决定主色）
  yinKey: {
    type: String,
    default: 'gong',
  },
  // 是否正在播放
  isPlaying: {
    type: Boolean,
    default: false,
  },
  // 播放进度 0-1
  progress: {
    type: Number,
    default: 0,
  },
  // 高度
  height: {
    type: String,
    default: '120px',
  },
})

// 五音 → 主色映射（与 HomeView/MusicDetailView 一致）
const YIN_COLORS = {
  gong: '#E8B8A8',
  shang: '#E8C5A8',
  jue: '#A8C5A0',
  zhi: '#E8A8B8',
  yu: '#A8B8C5',
}

// 5 音配色全集（每条曲线一个色）
const WAVE_COLORS = ['#E8B8A8', '#E8C5A8', '#A8C5A0', '#E8A8B8', '#A8B8C5']

const accentColor = computed(() => YIN_COLORS[props.yinKey] || YIN_COLORS.gong)
const shouldRenderCanvas = computed(() => shouldUseCanvas())

const canvasRef = ref(null)

let audioCtx = null
let analyser = null
let sourceNode = null
let freqData = null
let stopRAF = null
let enabled = false

const cleanup = []

// 暴露 connect 方法供父组件连接 audio 元素
const connect = (audioEl) => {
  if (!audioEl) return
  if (!shouldUseCanvas()) {
    enabled = false
    return
  }
  try {
    // 兼容 webkitAudioContext
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) {
      enabled = false
      return
    }
    if (!audioCtx) {
      audioCtx = new AC()
    }
    // audioCtx 被浏览器挂起时（自动播放策略）尝试恢复
    if (audioCtx.state === 'suspended') {
      audioCtx.resume().catch(() => {})
    }
    if (!sourceNode) {
      sourceNode = audioCtx.createMediaElementSource(audioEl)
      analyser = audioCtx.createAnalyser()
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.82
      sourceNode.connect(analyser)
      analyser.connect(audioCtx.destination)
      freqData = new Uint8Array(analyser.frequencyBinCount)
    }
    enabled = true
  } catch (e) {
    console.warn('[AudioVisualizer] Web Audio API unavailable', e)
    enabled = false
  }
}

defineExpose({ connect })

// ─── 渲染循环 ───
const startRender = () => {
  if (stopRAF) stopRAF()
  if (!shouldUseCanvas()) return

  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d', { alpha: true })
  if (!ctx) return

  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  const resize = () => {
    const w = canvas.clientWidth
    const h = canvas.clientHeight
    canvas.width = w * dpr
    canvas.height = h * dpr
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.scale(dpr, dpr)
  }
  resize()

  let resizeTimer = null
  const onResize = () => {
    if (resizeTimer) clearTimeout(resizeTimer)
    resizeTimer = setTimeout(resize, 150)
  }
  window.addEventListener('resize', onResize)
  cleanup.push(() => {
    window.removeEventListener('resize', onResize)
    if (resizeTimer) clearTimeout(resizeTimer)
  })

  // 移动端降帧率
  const fps = isMobile() ? 24 : 30
  const frameInterval = 1000 / fps
  let lastFrame = 0

  // 5 条波的相位偏移（每条独立漂动）
  const wavePhases = [0, 0.6, 1.2, 1.8, 2.4]

  const render = (ts) => {
    if (ts - lastFrame < frameInterval) {
      return
    }
    lastFrame = ts

    const w = canvas.clientWidth
    const h = canvas.clientHeight
    ctx.clearRect(0, 0, w, h)

    // 获取频谱数据（若未启用或未连接，用静默占位）
    let energy = 0
    if (enabled && analyser && freqData && props.isPlaying) {
      analyser.getByteFrequencyData(freqData)
      // 取低频段平均能量（更适合音波视觉）
      for (let i = 0; i < 32; i++) energy += freqData[i]
      energy = energy / (32 * 255)
    } else {
      // 待机：极低振幅呼吸
      energy = 0.04 + 0.02 * Math.sin(ts * 0.001)
    }

    // 5 条流动曲线
    for (let i = 0; i < 5; i++) {
      const color = WAVE_COLORS[i]
      const phase = wavePhases[i] + ts * 0.0008
      const baseAmp = h * 0.06 + energy * h * 0.28
      // 不同波振幅微调
      const ampMult = [1.0, 0.85, 0.92, 0.78, 0.88][i]
      const amp = baseAmp * ampMult
      const yCenter = h * (0.3 + i * 0.1)

      ctx.beginPath()
      ctx.moveTo(0, yCenter)
      for (let x = 0; x <= w; x += 4) {
        // 三层正弦叠加，柔和流动
        const y =
          yCenter +
          Math.sin(x * 0.012 + phase) * amp * 0.6 +
          Math.sin(x * 0.025 + phase * 1.4) * amp * 0.3 +
          Math.sin(x * 0.05 + phase * 0.7) * amp * 0.15
        ctx.lineTo(x, y)
      }
      ctx.strokeStyle = color
      ctx.globalAlpha = 0.5 + energy * 0.3
      ctx.lineWidth = 1.5
      ctx.stroke()

      // 下方半透明填充，增加质感
      ctx.lineTo(w, h)
      ctx.lineTo(0, h)
      ctx.closePath()
      ctx.fillStyle = color
      ctx.globalAlpha = 0.05 + energy * 0.06
      ctx.fill()
    }
    ctx.globalAlpha = 1

    // 进度条线（顶部细线）
    if (props.progress > 0) {
      ctx.fillStyle = accentColor.value
      ctx.globalAlpha = 0.35
      ctx.fillRect(0, 0, w * props.progress, 2)
      ctx.globalAlpha = 1
    }
  }
  stopRAF = smartRAF(render)
}

onMounted(() => {
  if (shouldUseCanvas()) {
    startRender()
  }
})

onBeforeUnmount(() => {
  if (stopRAF) stopRAF()
  cleanup.forEach((fn) => fn())
  if (sourceNode) {
    try { sourceNode.disconnect() } catch (_) {}
  }
  if (analyser) {
    try { analyser.disconnect() } catch (_) {}
  }
  if (audioCtx && audioCtx.state !== 'closed') {
    audioCtx.close().catch(() => {})
  }
})
</script>

<template>
  <div
    class="audio-visualizer"
    :style="{ height, '--accent': accentColor }"
    aria-hidden="true"
  >
    <!-- Canvas 主可视化（reduced-motion 关闭） -->
    <canvas v-if="shouldRenderCanvas" ref="canvasRef" class="audio-visualizer__canvas" />

    <!-- 降级：静态 5 色横条（reduced-motion 或无 Web Audio） -->
    <div v-else class="audio-visualizer__fallback">
      <div
        v-for="(c, i) in WAVE_COLORS"
        :key="i"
        class="audio-visualizer__bar"
        :style="{ background: c, animationDelay: i * 0.4 + 's' }"
      />
    </div>
  </div>
</template>

<style scoped>
.audio-visualizer {
  position: relative;
  width: 100%;
  border-radius: var(--radius-lg, 20px);
  overflow: hidden;
  background: linear-gradient(180deg, rgba(250, 248, 244, 0.6) 0%, rgba(232, 213, 168, 0.08) 100%);
  backdrop-filter: blur(8px);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.12));
}

.audio-visualizer__canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.audio-visualizer__fallback {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 24px;
}

.audio-visualizer__bar {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  opacity: 0.4;
  animation: barBreath 3.6s ease-in-out infinite;
}

@keyframes barBreath {
  0%, 100% { transform: scaleY(1); opacity: 0.3; }
  50% { transform: scaleY(1.6); opacity: 0.6; }
}

@media (prefers-reduced-motion: reduce) {
  .audio-visualizer__bar {
    animation: none;
    opacity: 0.4;
  }
}
</style>
