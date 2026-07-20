<script setup>
/**
 * AmbientBackground.vue — 全局治愈系氛围背景（v2 现代化重构）
 *
 * v2 升级要点（解决"红白机观感"和"交互不明确"两大问题）：
 *   1. 软光点 sprite 纹理：Canvas2D + Three.js 都用径向渐变圆点，替代粗糙方形点
 *   2. 鼠标交互：粒子受鼠标位置影响，靠近时柔和排斥（避免遮挡阅读）
 *   3. 滚动视差：Three.js 远景层根据 scrollY 产生 Y 轴偏移，增强景深
 *   4. 轻量 Bloom：Three.js 层叠加 UnrealBloomPass（强度 0.3，移动端 0.18）
 *   5. PBR 渲染器：ACES + sRGB，与 HeroScene/FlowerField 统一管线
 *   6. 完整释放：disposeRenderer + disposeObject3D 替代手写释放
 *
 * 三层渐进增强（保留 v1 策略，互不依赖）：
 *   1. CSS 雾气光斑（永远启用，GPU transform/opacity 加速）
 *      - 3 个大尺寸 radial-gradient blob，慢速漂移 + 呼吸
 *   2. Canvas2D 飘浮光点（reduced-motion 关闭）
 *      - 柔光径向渐变圆点 + 鼠标轻微排斥
 *   3. Three.js 远景粒子层（仅 WebGL + 非 reduced-motion + 非低性能）
 *      - sprite 纹理粒子 + Bloom + 滚动视差 + 鼠标跟随
 *
 * 集成位置：AppLayout.vue 根 div 第一层，position: fixed inset:0 z-index:-1
 * 不影响交互（pointer-events: none），不阻塞内容
 *
 * 4 铁律：shallowRef / smartRAF / onBeforeUnmount 完整释放 / 无音频源
 */
import { ref, onMounted, onBeforeUnmount, shallowRef } from 'vue'
import {
  shouldUseCanvas,
  shouldUseThreeJS,
  isMobile,
  smartRAF,
} from '@/utils/visual'
import {
  createRenderer,
  createPostProcessing,
  createSoftSpriteTexture,
  disposeObject3D,
  disposeRenderer,
} from '@/utils/three-helpers'

const canvasRef = ref(null)
const threeContainerRef = ref(null)
const three = shallowRef(null)

// 治愈系配色（与 FlowerField.vue 一致）
const MIST_COLORS = [
  'rgba(232, 184, 197, 0.35)',  // 藕粉
  'rgba(168, 197, 160, 0.30)',  // 青绿
  'rgba(168, 184, 197, 0.30)',  // 雾蓝
]

// ─── 鼠标位置（全局共享，Canvas2D 和 Three.js 都用） ───
const mouse = { x: -9999, y: -9999, tx: -9999, ty: -9999, active: false }
const onMouseMove = (e) => {
  mouse.tx = e.clientX
  mouse.ty = e.clientY
  if (!mouse.active) {
    mouse.active = true
    mouse.x = e.clientX
    mouse.y = e.clientY
  }
}
const onMouseLeave = () => {
  mouse.tx = -9999
  mouse.ty = -9999
  mouse.active = false
}

// ─── 滚动位置（Three.js 视差用） ───
const scroll = { y: 0, ty: 0 }
const onScroll = () => {
  scroll.ty = window.scrollY || 0
}

// ─── Canvas2D 飘浮光点（v2 升级：柔光径向渐变 + 鼠标排斥） ───
const initCanvasDust = () => {
  if (!shouldUseCanvas()) return
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d', { alpha: true })
  if (!ctx) return

  const mobile = isMobile()
  // 移动端粒子数减半
  const count = mobile ? 24 : 60
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
    ctx.setTransform(1, 0, 0, 1, 0, 0)
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
      a: 0.22 + Math.random() * 0.35,
      color,
      phase: Math.random() * Math.PI * 2,
      phaseSpeed: 0.002 + Math.random() * 0.004,
    })
  }

  // 预生成柔光圆点 sprite（径向渐变白色，绘制时用 globalAlpha 调亮度，multiply 颜色）
  const spriteSize = 32
  const spriteCanvas = document.createElement('canvas')
  spriteCanvas.width = spriteCanvas.height = spriteSize
  const sCtx = spriteCanvas.getContext('2d')
  const sGrad = sCtx.createRadialGradient(
    spriteSize / 2, spriteSize / 2, 0,
    spriteSize / 2, spriteSize / 2, spriteSize / 2,
  )
  sGrad.addColorStop(0, 'rgba(255,255,255,1)')
  sGrad.addColorStop(0.4, 'rgba(255,255,255,0.55)')
  sGrad.addColorStop(0.7, 'rgba(255,255,255,0.15)')
  sGrad.addColorStop(1, 'rgba(255,255,255,0)')
  sCtx.fillStyle = sGrad
  sCtx.fillRect(0, 0, spriteSize, spriteSize)

  let stopRAF = null
  const render = () => {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)

    // 平滑鼠标位置
    if (mouse.active) {
      mouse.x += (mouse.tx - mouse.x) * 0.08
      mouse.y += (mouse.ty - mouse.y) * 0.08
    }

    for (const p of particles) {
      // 鼠标排斥（半径 120px 内推开）
      if (mouse.active) {
        const dx = p.x - mouse.x
        const dy = p.y - mouse.y
        const distSq = dx * dx + dy * dy
        const radius = 120
        if (distSq < radius * radius && distSq > 0.01) {
          const dist = Math.sqrt(distSq)
          const force = (1 - dist / radius) * 0.6
          p.vx += (dx / dist) * force
          p.vy += (dy / dist) * force
        }
      }

      p.x += p.vx
      p.y += p.vy
      p.vx *= 0.985  // 阻尼，鼠标推开后逐渐回归
      p.vy = p.vy * 0.985 - 0.005  // 保留缓慢上升趋势
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
      const size = p.r * 4  // sprite 直径 = r * 4，让光晕更柔和

      // 用柔光 sprite 绘制（source-atop 合成模式 + 颜色叠加）
      ctx.globalAlpha = alpha
      ctx.globalCompositeOperation = 'source-over'
      // 先用 multiply 染色，再 normal 叠加
      ctx.drawImage(spriteCanvas, p.x - size / 2, p.y - size / 2, size, size)

      // 颜色叠加（柔光圆点本身是白色，这里叠一层色调）
      ctx.globalCompositeOperation = 'source-atop'
      ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.6)`
      ctx.beginPath()
      ctx.arc(p.x, p.y, size / 2, 0, Math.PI * 2)
      ctx.fill()
      ctx.globalCompositeOperation = 'source-over'
    }
    ctx.globalAlpha = 1
  }
  stopRAF = smartRAF(render)

  // resize 监听（防抖）
  let resizeTimer = null
  const onResize = () => {
    if (resizeTimer) clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      resize()
    }, 200)
  }
  window.addEventListener('resize', onResize)

  three.value = three.value || {}
  three.value._canvasCleanup = () => {
    if (stopRAF) stopRAF()
    window.removeEventListener('resize', onResize)
    if (resizeTimer) clearTimeout(resizeTimer)
  }
}

// ─── Three.js 远景粒子层（v2 升级：PBR + Bloom + 视差 + 鼠标跟随） ───
const initThreeDust = async () => {
  if (!shouldUseThreeJS()) return
  if (!threeContainerRef.value) return

  try {
    const THREE = await import('three')
    const container = threeContainerRef.value
    const mobile = isMobile()
    const w = window.innerWidth
    const h = window.innerHeight

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(60, w / h, 0.1, 100)
    camera.position.z = 14

    // ─── PBR 渲染器（统一管线） ───
    const canvas = document.createElement('canvas')
    container.appendChild(canvas)
    const renderer = createRenderer(canvas, {
      dpr: mobile ? 1.25 : 1.75,
      shadows: false,  // 全局背景不需要阴影
      toneMappingExposure: 1.05,
    })
    renderer.setSize(w, h)
    renderer.setClearColor(0x000000, 0)  // 透明背景，让 CSS 雾气透出来

    // ─── 轻量 Bloom（弱强度，避免抢戏） ───
    const composer = createPostProcessing(scene, camera, renderer, {
      strength: mobile ? 0.18 : 0.3,
      radius: 0.6,
      threshold: 0.75,
    })

    // ─── 远景柔光粒子（sprite 纹理） ───
    const dustCount = mobile ? 50 : 90
    const positions = new Float32Array(dustCount * 3)
    const colors = new Float32Array(dustCount * 3)
    const sizes = new Float32Array(dustCount)
    const originalY = new Float32Array(dustCount)  // 用于视差偏移
    const palette = [
      [0.91, 0.72, 0.77],  // 藕粉
      [0.91, 0.84, 0.66],  // 淡黄
      [0.66, 0.77, 0.63],  // 青绿
      [0.66, 0.72, 0.77],  // 雾蓝
      [0.98, 0.96, 0.95],  // 纯白
    ]
    for (let i = 0; i < dustCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 32
      const y = (Math.random() - 0.5) * 22
      positions[i * 3 + 1] = y
      originalY[i] = y
      positions[i * 3 + 2] = (Math.random() - 0.5) * 16 - 4
      const c = palette[Math.floor(Math.random() * palette.length)]
      colors[i * 3] = c[0]
      colors[i * 3 + 1] = c[1]
      colors[i * 3 + 2] = c[2]
      sizes[i] = 0.18 + Math.random() * 0.42
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))

    // 用 createSoftSpriteTexture 生成柔光 sprite
    const spriteTex = createSoftSpriteTexture(128, '#ffffff')
    const mat = new THREE.PointsMaterial({
      size: 0.6,
      map: spriteTex,
      vertexColors: true,
      transparent: true,
      opacity: 0.65,
      sizeAttenuation: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,  // 加法混合，让光点叠加更亮
    })
    const points = new THREE.Points(geo, mat)
    scene.add(points)

    // ─── 第二层：近景小粒子（更小、更密，制造层次感） ───
    const closeCount = mobile ? 20 : 35
    const closePos = new Float32Array(closeCount * 3)
    const closeColors = new Float32Array(closeCount * 3)
    for (let i = 0; i < closeCount; i++) {
      closePos[i * 3] = (Math.random() - 0.5) * 28
      closePos[i * 3 + 1] = (Math.random() - 0.5) * 18
      closePos[i * 3 + 2] = Math.random() * 6 + 2  // 离相机更近
      const c = palette[Math.floor(Math.random() * palette.length)]
      closeColors[i * 3] = c[0]
      closeColors[i * 3 + 1] = c[1]
      closeColors[i * 3 + 2] = c[2]
    }
    const closeGeo = new THREE.BufferGeometry()
    closeGeo.setAttribute('position', new THREE.BufferAttribute(closePos, 3))
    closeGeo.setAttribute('color', new THREE.BufferAttribute(closeColors, 3))
    const closeMat = new THREE.PointsMaterial({
      size: 0.18,
      map: spriteTex,
      vertexColors: true,
      transparent: true,
      opacity: 0.5,
      sizeAttenuation: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
    const closePoints = new THREE.Points(closeGeo, closeMat)
    scene.add(closePoints)

    // ─── 渲染循环（鼠标跟随 + 滚动视差） ───
    const follow = { x: 0, y: 0 }
    const clock = new THREE.Clock()
    let stopRAF = null
    const render = () => {
      const t = clock.getElapsedTime()

      // 平滑鼠标跟随（仅旋转，不位移，避免视觉抖动）
      if (mouse.active) {
        const targetX = (mouse.x / window.innerWidth - 0.5) * 2
        const targetY = (mouse.y / window.innerHeight - 0.5) * 2
        follow.x += (targetX - follow.x) * 0.04
        follow.y += (targetY - follow.y) * 0.04
      } else {
        follow.x *= 0.96
        follow.y *= 0.96
      }

      // 平滑滚动视差
      scroll.y += (scroll.ty - scroll.y) * 0.08

      // 远景层：旋转 + 视差 Y 偏移（视差系数小，景深远）
      points.rotation.y = t * 0.02 + follow.x * 0.18
      points.rotation.x = follow.y * 0.1
      points.position.y = scroll.y * 0.0008  // 远景视差系数小

      // 近景层：反向旋转 + 视差 Y 偏移更大（近景物镜移动快）
      closePoints.rotation.y = -t * 0.015 + follow.x * 0.3
      closePoints.rotation.x = follow.y * 0.18
      closePoints.position.y = scroll.y * 0.002  // 近景视差系数大

      composer.render()
    }
    stopRAF = smartRAF(render)

    const onResize = () => {
      const w2 = window.innerWidth
      const h2 = window.innerHeight
      camera.aspect = w2 / h2
      camera.updateProjectionMatrix()
      renderer.setSize(w2, h2)
      composer.setSize(w2, h2)
    }
    window.addEventListener('resize', onResize)

    three.value = three.value || {}
    three.value._threeCleanup = () => {
      if (stopRAF) stopRAF()
      window.removeEventListener('resize', onResize)
      // 释放 sprite 纹理（被两个 material 共享，dispose 一次即可）
      if (spriteTex) spriteTex.dispose()
      disposeObject3D(points)
      disposeObject3D(closePoints)
      disposeRenderer(renderer, composer)
      if (canvas && container.contains(canvas)) {
        container.removeChild(canvas)
      }
    }
  } catch (e) {
    // Three.js 加载/初始化失败 → 静默降级（Canvas2D + CSS 仍在）
    console.warn('[AmbientBackground] Three.js unavailable, fallback to CSS+Canvas', e)
  }
}

onMounted(async () => {
  // 全局监听鼠标 + 滚动（passive 提升性能）
  window.addEventListener('mousemove', onMouseMove, { passive: true })
  window.addEventListener('mouseleave', onMouseLeave, { passive: true })
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()  // 初始滚动位置

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
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseleave', onMouseLeave)
  window.removeEventListener('scroll', onScroll)
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
