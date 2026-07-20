<script setup>
/**
 * AudioVisualizer.vue — 5 色音波可视化（v2 多模式升级）
 *
 * v2 升级要点（解决"交互不明确"和"视觉粗糙"两大问题）：
 *   1. 4 种可视化模式，点击 canvas 循环切换：
 *      - wave: 流动波形（v1 默认，柔和 5 色曲线）
 *      - mirror: 镜像柱状（上下对称频谱柱，Apple Music 风格）
 *      - radial: 径向频谱（圆形从中心向外发射，360° 可视化）
 *      - particles: 粒子流（频谱驱动粒子跳动）
 *   2. 节拍检测：低频能量突增 → 触发粒子爆裂
 *   3. 频率响应颜色：低频强 → 暖色（宫/徵），高频强 → 冷色（羽/商）
 *   4. 模式切换 toast 提示（顶部居中浮现 1.2s）
 *   5. 平滑过渡：模式切换淡入淡出
 *   6. 增大默认高度（120px → 160px）
 *
 * 保留（v1 设计）：
 *   - Web Audio API AnalyserNode（fftSize=256）
 *   - createMediaElementSource 一次性约束（if (!sourceNode) 守卫）
 *   - 30fps 渲染（移动端 24fps），smartRAF 标签页隐藏暂停
 *   - reduced-motion / 无 Web Audio → 静态 5 色横条降级
 *   - 待机呼吸模式（未播放时极低振幅）
 */
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { shouldUseCanvas, isMobile, smartRAF } from '@/utils/visual'

const props = defineProps({
  yinKey: {
    type: String,
    default: 'gong',
  },
  isPlaying: {
    type: Boolean,
    default: false,
  },
  progress: {
    type: Number,
    default: 0,
  },
  height: {
    type: String,
    default: '160px',
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

// 4 种模式定义
const MODES = [
  { key: 'wave', name: '流动波形' },
  { key: 'mirror', name: '镜像柱状' },
  { key: 'radial', name: '径向频谱' },
  { key: 'particles', name: '粒子流' },
]

const accentColor = computed(() => YIN_COLORS[props.yinKey] || YIN_COLORS.gong)
const shouldRenderCanvas = computed(() => shouldUseCanvas())

const canvasRef = ref(null)
const currentMode = ref(0)  // 0-3，对应 MODES 索引
const modeToast = ref('')   // 模式切换提示
let modeToastTimer = null

let audioCtx = null
let analyser = null
let sourceNode = null
let freqData = null
let stopRAF = null
let enabled = false

// 节拍检测 + 粒子爆裂状态
let lastBassEnergy = 0
let beatParticles = []  // { x, y, vx, vy, life, color }

const cleanup = []

// 暴露 connect 方法供父组件连接 audio 元素
const connect = (audioEl) => {
  if (!audioEl) return
  if (!shouldUseCanvas()) {
    enabled = false
    return
  }
  try {
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) {
      enabled = false
      return
    }
    if (!audioCtx) {
      audioCtx = new AC()
    }
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

// 点击 canvas 切换模式
const onCanvasClick = () => {
  currentMode.value = (currentMode.value + 1) % MODES.length
  modeToast.value = MODES[currentMode.value].name
  if (modeToastTimer) clearTimeout(modeToastTimer)
  modeToastTimer = setTimeout(() => {
    modeToast.value = ''
  }, 1400)
}

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

  const fps = isMobile() ? 24 : 30
  const frameInterval = 1000 / fps
  let lastFrame = 0

  // 5 条波的相位偏移
  const wavePhases = [0, 0.6, 1.2, 1.8, 2.4]

  const render = (ts) => {
    if (ts - lastFrame < frameInterval) {
      return
    }
    lastFrame = ts

    const w = canvas.clientWidth
    const h = canvas.clientHeight
    ctx.clearRect(0, 0, w, h)

    // 获取频谱数据
    let bassEnergy = 0
    let midEnergy = 0
    let highEnergy = 0
    let totalEnergy = 0

    if (enabled && analyser && freqData && props.isPlaying) {
      analyser.getByteFrequencyData(freqData)
      // 低频 0-8（bass），中频 8-32（mid），高频 32-128（high）
      for (let i = 0; i < 8; i++) bassEnergy += freqData[i]
      for (let i = 8; i < 32; i++) midEnergy += freqData[i]
      for (let i = 32; i < 128; i++) highEnergy += freqData[i]
      bassEnergy = bassEnergy / (8 * 255)
      midEnergy = midEnergy / (24 * 255)
      highEnergy = highEnergy / (96 * 255)
      totalEnergy = (bassEnergy + midEnergy + highEnergy) / 3
    } else {
      // 待机：极低振幅呼吸
      bassEnergy = 0.04 + 0.02 * Math.sin(ts * 0.001)
      midEnergy = 0.04 + 0.02 * Math.sin(ts * 0.0013 + 1)
      highEnergy = 0.04 + 0.02 * Math.sin(ts * 0.0016 + 2)
      totalEnergy = 0.04
    }

    // 节拍检测：bass 突增
    if (props.isPlaying && bassEnergy > lastBassEnergy * 1.35 && bassEnergy > 0.35) {
      // 触发粒子爆裂
      const cx = w * 0.5
      const cy = h * 0.5
      const burstCount = isMobile() ? 6 : 10
      for (let i = 0; i < burstCount; i++) {
        const angle = (Math.PI * 2 * i) / burstCount + Math.random() * 0.3
        const speed = 1.2 + Math.random() * 1.8
        beatParticles.push({
          x: cx,
          y: cy,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 1.0,
          color: WAVE_COLORS[Math.floor(Math.random() * WAVE_COLORS.length)],
        })
      }
    }
    lastBassEnergy = bassEnergy

    // 频响主色：低频强 → 暖色（gong/zhi），高频强 → 冷色（yu/shang）
    const warmWeight = bassEnergy + midEnergy * 0.5
    const coolWeight = highEnergy + midEnergy * 0.5
    let dominantColor
    if (warmWeight > coolWeight * 1.15) {
      dominantColor = YIN_COLORS.gong  // 暖
    } else if (coolWeight > warmWeight * 1.15) {
      dominantColor = YIN_COLORS.yu  // 冷
    } else {
      dominantColor = accentColor.value
    }

    // 根据当前模式渲染
    const mode = MODES[currentMode.value].key
    switch (mode) {
      case 'wave':
        renderWave(ctx, w, h, ts, totalEnergy)
        break
      case 'mirror':
        renderMirror(ctx, w, h, freqData, totalEnergy, dominantColor, props.isPlaying)
        break
      case 'radial':
        renderRadial(ctx, w, h, ts, freqData, totalEnergy, dominantColor, props.isPlaying)
        break
      case 'particles':
        renderParticles(ctx, w, h, ts, freqData, totalEnergy, dominantColor, props.isPlaying)
        break
    }

    // 节拍粒子（所有模式通用）
    renderBeatParticles(ctx)

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

// ─── 模式 1：流动波形（v1 保留） ───
const renderWave = (ctx, w, h, ts, energy) => {
  for (let i = 0; i < 5; i++) {
    const color = WAVE_COLORS[i]
    const phase = wavePhases[i] + ts * 0.0008
    const baseAmp = h * 0.06 + energy * h * 0.28
    const ampMult = [1.0, 0.85, 0.92, 0.78, 0.88][i]
    const amp = baseAmp * ampMult
    const yCenter = h * (0.3 + i * 0.1)

    ctx.beginPath()
    ctx.moveTo(0, yCenter)
    for (let x = 0; x <= w; x += 4) {
      const y =
        yCenter +
        Math.sin(x * 0.012 + phase) * amp * 0.6 +
        Math.sin(x * 0.025 + phase * 1.4) * amp * 0.3 +
        Math.sin(x * 0.05 + phase * 0.7) * amp * 0.15
      ctx.lineTo(x, y)
    }
    ctx.strokeStyle = color
    ctx.globalAlpha = 0.55 + energy * 0.3
    ctx.lineWidth = 1.8
    ctx.lineCap = 'round'
    ctx.stroke()

    // 下方半透明填充
    ctx.lineTo(w, h)
    ctx.lineTo(0, h)
    ctx.closePath()
    ctx.fillStyle = color
    ctx.globalAlpha = 0.06 + energy * 0.08
    ctx.fill()
  }
  ctx.globalAlpha = 1
}

// ─── 模式 2：镜像柱状（上下对称） ───
const renderMirror = (ctx, w, h, freqData, energy, dominantColor, isPlaying) => {
  if (!freqData || !isPlaying) {
    // 待机：画 32 根静态柱
    const bars = 32
    const barW = w / bars * 0.7
    const gap = w / bars * 0.3
    const cy = h * 0.5
    for (let i = 0; i < bars; i++) {
      const x = i * (barW + gap) + gap * 0.5
      const amp = h * 0.04 * (0.5 + 0.5 * Math.sin(i * 0.3 + Date.now() * 0.001))
      ctx.fillStyle = WAVE_COLORS[i % 5]
      ctx.globalAlpha = 0.4
      ctx.fillRect(x, cy - amp, barW, amp * 2)
    }
    ctx.globalAlpha = 1
    return
  }

  const bars = 48
  const barW = w / bars * 0.7
  const gap = w / bars * 0.3
  const cy = h * 0.5
  const maxBarH = h * 0.42

  for (let i = 0; i < bars; i++) {
    // 从 freqData 采样（前 80% 频段，避免高频空数据）
    const idx = Math.floor((i / bars) * freqData.length * 0.8)
    const v = freqData[idx] / 255
    const amp = Math.max(2, v * maxBarH * (0.6 + energy * 0.6))
    const x = i * (barW + gap) + gap * 0.5

    // 渐变色：低频暖色，高频冷色
    const t = i / bars
    const color = t < 0.5
      ? WAVE_COLORS[Math.floor(t * 2 * 2) % 2]  // 暖色（gong/shang）
      : WAVE_COLORS[2 + Math.floor((t - 0.5) * 2 * 2) % 3]  // 冷色（jue/zhi/yu）

    // 上半部分
    const grad1 = ctx.createLinearGradient(0, cy - amp, 0, cy)
    grad1.addColorStop(0, color)
    grad1.addColorStop(1, dominantColor)
    ctx.fillStyle = grad1
    ctx.globalAlpha = 0.85
    ctx.fillRect(x, cy - amp, barW, amp)

    // 下半部分（镜像，透明度降低）
    const grad2 = ctx.createLinearGradient(0, cy, 0, cy + amp)
    grad2.addColorStop(0, dominantColor)
    grad2.addColorStop(1, color)
    ctx.fillStyle = grad2
    ctx.globalAlpha = 0.5
    ctx.fillRect(x, cy, barW, amp)
  }
  ctx.globalAlpha = 1

  // 中线
  ctx.strokeStyle = dominantColor
  ctx.globalAlpha = 0.2
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(0, cy)
  ctx.lineTo(w, cy)
  ctx.stroke()
  ctx.globalAlpha = 1
}

// ─── 模式 3：径向频谱（360°） ───
const renderRadial = (ctx, w, h, ts, freqData, energy, dominantColor, isPlaying) => {
  const cx = w * 0.5
  const cy = h * 0.5
  const innerR = Math.min(w, h) * 0.18
  const maxBarLen = Math.min(w, h) * 0.32

  // 中心圆（呼吸）
  const breathR = innerR * (1 + 0.05 * Math.sin(ts * 0.002))
  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, breathR)
  grad.addColorStop(0, dominantColor)
  grad.addColorStop(0.6, dominantColor + '88')
  grad.addColorStop(1, dominantColor + '00')
  ctx.fillStyle = grad
  ctx.globalAlpha = 0.6 + energy * 0.3
  ctx.beginPath()
  ctx.arc(cx, cy, breathR, 0, Math.PI * 2)
  ctx.fill()

  // 径向柱
  const bars = 64
  if (freqData && isPlaying) {
    for (let i = 0; i < bars; i++) {
      const idx = Math.floor((i / bars) * freqData.length * 0.8)
      const v = freqData[idx] / 255
      const amp = Math.max(2, v * maxBarLen * (0.5 + energy * 0.7))
      const angle = (i / bars) * Math.PI * 2 - Math.PI / 2 + ts * 0.0001

      const x1 = cx + Math.cos(angle) * innerR
      const y1 = cy + Math.sin(angle) * innerR
      const x2 = cx + Math.cos(angle) * (innerR + amp)
      const y2 = cy + Math.sin(angle) * (innerR + amp)

      const t = i / bars
      const color = t < 0.5
        ? WAVE_COLORS[Math.floor(t * 2 * 2) % 2]
        : WAVE_COLORS[2 + Math.floor((t - 0.5) * 2 * 2) % 3]

      ctx.strokeStyle = color
      ctx.globalAlpha = 0.85
      ctx.lineWidth = 2.5
      ctx.lineCap = 'round'
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.stroke()
    }
  } else {
    // 待机：静态径向柱
    for (let i = 0; i < bars; i++) {
      const amp = maxBarLen * 0.1 * (0.5 + 0.5 * Math.sin(i * 0.4 + ts * 0.001))
      const angle = (i / bars) * Math.PI * 2 - Math.PI / 2
      const x1 = cx + Math.cos(angle) * innerR
      const y1 = cy + Math.sin(angle) * innerR
      const x2 = cx + Math.cos(angle) * (innerR + amp)
      const y2 = cy + Math.sin(angle) * (innerR + amp)
      ctx.strokeStyle = WAVE_COLORS[i % 5]
      ctx.globalAlpha = 0.35
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.stroke()
    }
  }
  ctx.globalAlpha = 1
}

// ─── 模式 4：粒子流 ───
let flowParticles = null
const renderParticles = (ctx, w, h, ts, freqData, energy, dominantColor, isPlaying) => {
  const particleCount = isMobile() ? 60 : 120

  // 初始化粒子（首次或尺寸变化）
  if (!flowParticles || flowParticles.length !== particleCount) {
    flowParticles = []
    for (let i = 0; i < particleCount; i++) {
      flowParticles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: 1 + Math.random() * 2,
        colorIdx: Math.floor(Math.random() * 5),
      })
    }
  }

  // 拖尾效果：半透明覆盖
  ctx.fillStyle = 'rgba(250, 248, 244, 0.15)'
  ctx.fillRect(0, 0, w, h)

  for (let i = 0; i < particleCount; i++) {
    const p = flowParticles[i]
    // 频谱驱动跳动
    let amp = 1
    if (freqData && isPlaying) {
      const idx = Math.floor((i / particleCount) * freqData.length * 0.8)
      amp = 1 + (freqData[idx] / 255) * 3
    } else {
      amp = 1 + 0.3 * Math.sin(ts * 0.002 + i)
    }

    // 移动
    p.x += p.vx * amp
    p.y += p.vy * amp

    // 边界回弹
    if (p.x < 0 || p.x > w) p.vx *= -1
    if (p.y < 0 || p.y > h) p.vy *= -1
    p.x = Math.max(0, Math.min(w, p.x))
    p.y = Math.max(0, Math.min(h, p.y))

    // 绘制（带光晕）
    const color = WAVE_COLORS[p.colorIdx]
    const r = p.size * amp
    const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 3)
    grad.addColorStop(0, color)
    grad.addColorStop(0.4, color + 'aa')
    grad.addColorStop(1, color + '00')
    ctx.fillStyle = grad
    ctx.globalAlpha = 0.6 + energy * 0.3
    ctx.beginPath()
    ctx.arc(p.x, p.y, r * 3, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1
}

// ─── 节拍粒子（通用） ───
const renderBeatParticles = (ctx) => {
  for (let i = beatParticles.length - 1; i >= 0; i--) {
    const p = beatParticles[i]
    p.x += p.vx
    p.y += p.vy
    p.vx *= 0.96
    p.vy *= 0.96
    p.life -= 0.025
    if (p.life <= 0) {
      beatParticles.splice(i, 1)
      continue
    }
    ctx.fillStyle = p.color
    ctx.globalAlpha = p.life * 0.8
    ctx.beginPath()
    ctx.arc(p.x, p.y, 2 + p.life * 2, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1
}

onMounted(() => {
  if (shouldUseCanvas()) {
    startRender()
  }
})

onBeforeUnmount(() => {
  if (stopRAF) stopRAF()
  cleanup.forEach((fn) => fn())
  if (modeToastTimer) clearTimeout(modeToastTimer)
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
  >
    <!-- Canvas 主可视化（reduced-motion 关闭） -->
    <canvas
      v-if="shouldRenderCanvas"
      ref="canvasRef"
      class="audio-visualizer__canvas"
      @click="onCanvasClick"
    />

    <!-- 模式切换提示 toast -->
    <transition name="mode-toast">
      <div v-if="modeToast" class="audio-visualizer__mode-toast">
        <span class="mode-toast__icon">♪</span>
        <span class="mode-toast__text">{{ modeToast }}</span>
      </div>
    </transition>

    <!-- 模式切换指引（首次进入显示） -->
    <div v-if="shouldRenderCanvas" class="audio-visualizer__hint">
      <span>点击切换可视化模式</span>
    </div>

    <!-- 降级：静态 5 色横条（reduced-motion 或无 Web Audio） -->
    <div v-if="!shouldRenderCanvas" class="audio-visualizer__fallback">
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
  background: linear-gradient(180deg, rgba(250, 248, 244, 0.7) 0%, rgba(232, 213, 168, 0.1) 100%);
  backdrop-filter: blur(8px);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.12));
}

.audio-visualizer__canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  cursor: pointer;
}

/* 模式切换 toast */
.audio-visualizer__mode-toast {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  box-shadow: 0 8px 28px rgba(74, 68, 56, 0.18);
  pointer-events: none;
  z-index: 4;
  white-space: nowrap;
}

.mode-toast__icon {
  font-size: 16px;
  color: var(--accent, #B8A590);
}

.mode-toast__text {
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-primary, #3D3327);
  letter-spacing: 0.1em;
}

.mode-toast-enter-active,
.mode-toast-leave-active {
  transition: opacity 0.35s var(--ease-apple, cubic-bezier(0.16, 1, 0.3, 1)),
              transform 0.35s var(--ease-apple, cubic-bezier(0.16, 1, 0.3, 1));
}
.mode-toast-enter-from,
.mode-toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.92);
}

/* 模式切换指引（持续显示，淡出） */
.audio-visualizer__hint {
  position: absolute;
  bottom: 8px;
  right: 14px;
  font-family: var(--font-serif, serif);
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.08em;
  pointer-events: none;
  z-index: 3;
  opacity: 0.6;
  animation: hint-fade-out 8s ease-out forwards;
}

@keyframes hint-fade-out {
  0%, 70% { opacity: 0.6; }
  100% { opacity: 0; }
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

@media (max-width: 640px) {
  .audio-visualizer__mode-toast {
    padding: 8px 18px;
  }
  .mode-toast__text {
    font-size: 12px;
  }
  .audio-visualizer__hint {
    font-size: 10px;
    bottom: 6px;
    right: 10px;
  }
}
</style>
