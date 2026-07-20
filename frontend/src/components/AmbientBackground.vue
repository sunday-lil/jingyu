<script setup>
/**
 * AmbientBackground.vue — 全局治愈系氛围背景
 *
 * 三层渐进增强（每层独立降级，互不依赖）：
 *   1. CSS 雾气光斑（永远启用，GPU 加速 transform/opacity）
 *      - 3 个大尺寸 radial-gradient blob，慢速漂移 + 呼吸
 *      - 配色延续项目 mist/ink/五音色 token
 *   2. Canvas2D 飘浮光点（reduced-motion 关闭）
 *      - 24~60 个治愈色小点，缓慢上升 + 横向漂移
 *      - smartRAF：标签页隐藏自动暂停
 *   3. Three.js 远景粒子层（仅 WebGL + 非 reduced-motion + 非低性能）
 *      - 异步 import('three')，~80 个 sprite 粒子做景深光斑
 *      - 与 FlowerField.vue 共享 three-vendor chunk
 *
 * 集成位置：AppLayout.vue 根 div 第一层，position: fixed inset:0 z-index:-1
 * 不影响交互（pointer-events: none），不阻塞内容（absolute 而非 relative）
 */
import { ref, onMounted, onBeforeUnmount, shallowRef } from 'vue'
import {
  shouldUseCanvas,
  shouldUseThreeJS,
  isMobile,
  smartRAF,
} from '@/utils/visual'

const canvasRef = ref(null)
const threeContainerRef = ref(null)
const three = shallowRef(null)

// 治愈系配色（与 FlowerField.vue 一致）
const MIST_COLORS = [
  'rgba(232, 184, 197, 0.35)',  // 藕粉
  'rgba(168, 197, 160, 0.30)',  // 青绿
  'rgba(168, 184, 197, 0.30)',  // 雾蓝
]

// ─── Canvas2D 飘浮光点 ───
const initCanvasDust = () => {
  if (!shouldUseCanvas()) return
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d', { alpha: true })
  if (!ctx) return

  // 移动端粒子数减半
  const count = isMobile() ? 24 : 60
  const colors = [
    [232, 184, 197],  // 藕粉
    [232, 213, 168],  // 淡黄
    [168, 197, 160],  // 青绿
    [168, 184, 197],  // 雾蓝
    [250, 246, 242],  // 纯白
  ]

  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  const resize = () => {
    canvas.width = window.innerWidth * dpr
    canvas.height = window.innerHeight * dpr
    canvas.style.width = window.innerWidth + 'px'
    canvas.style.height = window.innerHeight + 'px'
    ctx.scale(dpr, dpr)
  }
  resize()

  // 生成粒子
  const particles = []
  for (let i = 0; i < count; i++) {
    const color = colors[Math.floor(Math.random() * colors.length)]
    particles.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: 0.8 + Math.random() * 2.4,
      vx: (Math.random() - 0.5) * 0.12,
      vy: -(0.05 + Math.random() * 0.18),  // 缓慢上升
      a: 0.18 + Math.random() * 0.32,
      color,
      phase: Math.random() * Math.PI * 2,
      phaseSpeed: 0.002 + Math.random() * 0.004,
    })
  }

  let stopRAF = null
  const render = () => {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)
    for (const p of particles) {
      p.x += p.vx
      p.y += p.vy
      p.phase += p.phaseSpeed
      // 边界回绕
      if (p.y < -10) {
        p.y = window.innerHeight + 10
        p.x = Math.random() * window.innerWidth
      }
      if (p.x < -10) p.x = window.innerWidth + 10
      if (p.x > window.innerWidth + 10) p.x = -10
      // 呼吸闪烁
      const alpha = p.a * (0.6 + 0.4 * Math.sin(p.phase))
      const [r, g, b] = p.color
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`
      ctx.fill()
    }
  }
  stopRAF = smartRAF(render)

  // resize 监听（防抖）
  let resizeTimer = null
  const onResize = () => {
    if (resizeTimer) clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      ctx.setTransform(1, 0, 0, 1, 0, 0)  // 重置 scale
      resize()
    }, 200)
  }
  window.addEventListener('resize', onResize)

  // 清理函数挂到 three 上以便统一调用
  three.value = three.value || {}
  three.value._canvasCleanup = () => {
    if (stopRAF) stopRAF()
    window.removeEventListener('resize', onResize)
    if (resizeTimer) clearTimeout(resizeTimer)
  }
}

// ─── Three.js 远景粒子层（可选，最高级） ───
const initThreeDust = async () => {
  if (!shouldUseThreeJS()) return
  if (!threeContainerRef.value) return

  try {
    const THREE = await import('three')
    const container = threeContainerRef.value
    const w = window.innerWidth
    const h = window.innerHeight

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(60, w / h, 0.1, 100)
    camera.position.z = 12

    const renderer = new THREE.WebGLRenderer({
      antialias: false,
      alpha: true,
      powerPreference: 'low-power',
    })
    renderer.setSize(w, h)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
    container.appendChild(renderer.domElement)

    // 远景雾化光斑（80 个 sprite）
    const dustCount = 80
    const positions = new Float32Array(dustCount * 3)
    const colors = new Float32Array(dustCount * 3)
    const sizes = new Float32Array(dustCount)
    const palette = [
      [0.91, 0.72, 0.77],  // 藕粉
      [0.91, 0.84, 0.66],  // 淡黄
      [0.66, 0.77, 0.63],  // 青绿
      [0.66, 0.72, 0.77],  // 雾蓝
      [0.98, 0.96, 0.95],  // 纯白
    ]
    for (let i = 0; i < dustCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 30
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20
      positions[i * 3 + 2] = (Math.random() - 0.5) * 15 - 5
      const c = palette[Math.floor(Math.random() * palette.length)]
      colors[i * 3] = c[0]
      colors[i * 3 + 1] = c[1]
      colors[i * 3 + 2] = c[2]
      sizes[i] = 0.15 + Math.random() * 0.35
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    const mat = new THREE.PointsMaterial({
      size: 0.3,
      vertexColors: true,
      transparent: true,
      opacity: 0.45,
      sizeAttenuation: true,
      depthWrite: false,
    })
    const points = new THREE.Points(geo, mat)
    scene.add(points)

    // 慢速旋转 + 鼠标跟随
    const mouse = { x: 0, y: 0, tx: 0, ty: 0 }
    const onMouse = (e) => {
      mouse.tx = (e.clientX / window.innerWidth - 0.5) * 2
      mouse.ty = (e.clientY / window.innerHeight - 0.5) * 2
    }
    window.addEventListener('mousemove', onMouse, { passive: true })

    const clock = new THREE.Clock()
    let stopRAF = null
    const render = () => {
      const t = clock.getElapsedTime()
      mouse.x += (mouse.tx - mouse.x) * 0.02
      mouse.y += (mouse.ty - mouse.y) * 0.02
      points.rotation.y = t * 0.02 + mouse.x * 0.15
      points.rotation.x = mouse.y * 0.1
      renderer.render(scene, camera)
    }
    stopRAF = smartRAF(render)

    const onResize = () => {
      const w2 = window.innerWidth
      const h2 = window.innerHeight
      camera.aspect = w2 / h2
      camera.updateProjectionMatrix()
      renderer.setSize(w2, h2)
    }
    window.addEventListener('resize', onResize)

    three.value = three.value || {}
    three.value._threeCleanup = () => {
      if (stopRAF) stopRAF()
      window.removeEventListener('mousemove', onMouse)
      window.removeEventListener('resize', onResize)
      geo.dispose()
      mat.dispose()
      renderer.dispose()
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  } catch (e) {
    // Three.js 加载/初始化失败 → 静默降级（Canvas2D + CSS 仍在）
    console.warn('[AmbientBackground] Three.js unavailable, fallback to CSS+Canvas')
  }
}

onMounted(async () => {
  // 先启 Canvas2D（中量级，几乎都跑得动）
  initCanvasDust()
  // 再尝试 Three.js（重量级，按需异步加载）
  await initThreeDust()
})

onBeforeUnmount(() => {
  const t = three.value
  if (!t) return
  if (t._canvasCleanup) t._canvasCleanup()
  if (t._threeCleanup) t._threeCleanup()
})
</script>

<template>
  <div class="ambient-bg" aria-hidden="true">
    <!-- 第 1 层：CSS 雾气光斑（永远启用） -->
    <div class="ambient-bg__mist-layer">
      <div
        v-for="(color, i) in MIST_COLORS"
        :key="i"
        class="ambient-bg__mist"
        :style="{ '--mist-color': color, '--mist-delay': i * -8 + 's' }"
      />
    </div>

    <!-- 第 2 层：Canvas2D 飘浮光点（reduced-motion 关闭） -->
    <canvas ref="canvasRef" class="ambient-bg__canvas" />

    <!-- 第 3 层：Three.js 远景粒子（按需加载） -->
    <div ref="threeContainerRef" class="ambient-bg__three" />
  </div>
</template>

<style scoped>
.ambient-bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  overflow: hidden;
  background: linear-gradient(180deg, #FAF8F4 0%, #F9F6F0 50%, #F0EDE5 100%);
}

/* ── 第 1 层：CSS 雾气光斑 ── */
.ambient-bg__mist-layer {
  position: absolute;
  inset: 0;
}
.ambient-bg__mist {
  position: absolute;
  width: 60vw;
  height: 60vw;
  max-width: 800px;
  max-height: 800px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--mist-color) 0%, transparent 70%);
  filter: blur(40px);
  opacity: 0.6;
  animation: mistDrift 24s ease-in-out infinite;
}
.ambient-bg__mist:nth-child(1) {
  top: -10%;
  left: -10%;
  animation-delay: var(--mist-delay, 0s);
}
.ambient-bg__mist:nth-child(2) {
  top: 40%;
  right: -15%;
  animation-delay: var(--mist-delay, -8s);
}
.ambient-bg__mist:nth-child(3) {
  bottom: -20%;
  left: 30%;
  animation-delay: var(--mist-delay, -16s);
}

@keyframes mistDrift {
  0%, 100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.55;
  }
  33% {
    transform: translate(40px, -30px) scale(1.08);
    opacity: 0.7;
  }
  66% {
    transform: translate(-30px, 40px) scale(0.95);
    opacity: 0.5;
  }
}

/* ── 第 2 层：Canvas2D ── */
.ambient-bg__canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

/* ── 第 3 层：Three.js 容器 ── */
.ambient-bg__three {
  position: absolute;
  inset: 0;
}
.ambient-bg__three :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}

/* ── reduced-motion：只保留 CSS 静态光斑 ── */
@media (prefers-reduced-motion: reduce) {
  .ambient-bg__mist {
    animation: none;
    opacity: 0.4;
  }
  .ambient-bg__canvas,
  .ambient-bg__three {
    display: none;
  }
}

/* ── 移动端：减少雾斑尺寸，降低视觉负担 ── */
@media (max-width: 768px) {
  .ambient-bg__mist {
    width: 80vw;
    height: 80vw;
    filter: blur(30px);
  }
}
</style>
