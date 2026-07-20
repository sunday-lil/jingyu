<script setup>
/**
 * HeroScene.vue — HomeView Hero 区的 3D 浮岛雾海场景
 *
 * 主题呼应："海上有座岛，岛上有人听" — 静屿的核心意象
 *
 * 场景构成（性能预算 < 4ms/frame）：
 *   1. 波动海面：128×128 PlaneGeometry + 顶点位移 shader（柔和正弦叠加）
 *   2. 浮岛 ×3：ConeGeometry + ConeGeometry，按治愈色（藕粉 / 青绿 / 雾蓝）着色
 *   3. 远景雾：FogExp2 让远岛融入天光
 *   4. 暖色方向光 + 半球光，午后阳光感
 *
 * 交互：
 *   - 鼠标移动 → 相机轻微视差
 *   - 自动呼吸式相机摆动
 *
 * 渐进降级：
 *   - 不支持 WebGL / reduced-motion / 低性能 → 显示 SVG 静态浮岛插画
 *   - Three.js 加载失败 → 静默回退到 SVG
 *
 * 异步加载：defineAsyncComponent 已由调用方处理（与 FlowerField 同套路）
 */
import { ref, onMounted, onBeforeUnmount, shallowRef } from 'vue'
import {
  shouldUseThreeJS,
  isMobile,
  smartRAF,
} from '@/utils/visual'

const props = defineProps({
  height: {
    type: String,
    default: '480px',
  },
})

const containerRef = ref(null)
const fallbackRef = ref(null)
const showThree = ref(false)
const showFallback = ref(false)

const three = shallowRef(null)

onMounted(async () => {
  if (!shouldUseThreeJS() || !containerRef.value) {
    // 直接走 SVG 降级
    showFallback.value = true
    return
  }
  try {
    await initScene()
    showThree.value = true
  } catch (e) {
    console.warn('[HeroScene] init failed, fallback to SVG', e)
    showFallback.value = true
  }
})

const initScene = async () => {
  const THREE = await import('three')
  const container = containerRef.value
  if (!container) return

  const width = container.clientWidth
  const height = container.clientHeight

  // ─── 场景 ───
  const scene = new THREE.Scene()
  scene.background = null  // 透明，让 CSS 渐变穿透
  scene.fog = new THREE.FogExp2(0xF9F6F0, 0.04)

  // ─── 相机 ───
  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100)
  camera.position.set(0, 4, 12)
  camera.lookAt(0, 1, 0)

  // ─── 渲染器 ───
  const renderer = new THREE.WebGLRenderer({
    antialias: !isMobile(),
    alpha: true,
    powerPreference: 'high-performance',
  })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  container.appendChild(renderer.domElement)

  // ─── 光照 ───
  const ambient = new THREE.AmbientLight(0xFFEEDD, 0.6)
  scene.add(ambient)
  const sun = new THREE.DirectionalLight(0xFFF5E0, 1.0)
  sun.position.set(6, 10, 4)
  scene.add(sun)
  const hemi = new THREE.HemisphereLight(0xF5E8D5, 0x8B7B5E, 0.4)
  scene.add(hemi)

  // ─── 波动海面 ───
  // 移动端降分辨率
  const segs = isMobile() ? 64 : 128
  const seaGeo = new THREE.PlaneGeometry(40, 40, segs, segs)
  seaGeo.rotateX(-Math.PI / 2)
  // 保存原始顶点位置供 shader 位移
  const seaPositions = seaGeo.attributes.position.array.slice(0)
  const seaMat = new THREE.MeshLambertMaterial({
    color: 0xA8C5C8,
    transparent: true,
    opacity: 0.55,
    flatShading: false,
  })
  const sea = new THREE.Mesh(seaGeo, seaMat)
  sea.position.y = -0.5
  scene.add(sea)

  // ─── 浮岛 ×3 ───
  const islands = []
  const islandColors = [0xE8B8C5, 0xA8C5A0, 0xA8B8C5]  // 藕粉 / 青绿 / 雾蓝
  const islandPositions = [
    { x: 0, y: 1.5, z: 0, scale: 1.0 },
    { x: -4.5, y: 2.6, z: -2, scale: 0.55 },
    { x: 4.8, y: 2.1, z: -1.5, scale: 0.7 },
  ]
  for (let i = 0; i < 3; i++) {
    const islandGroup = new THREE.Group()

    // 岛底（倒锥，像悬浮的岩块）
    const baseGeo = new THREE.ConeGeometry(1.2, 1.6, 8)
    const baseMat = new THREE.MeshLambertMaterial({
      color: 0x8B7B5E,
      flatShading: true,
    })
    const base = new THREE.Mesh(baseGeo, baseMat)
    base.position.y = -0.6
    base.rotation.y = Math.PI  // 倒过来：尖端朝下
    islandGroup.add(base)

    // 岛顶（草地色扁圆）
    const topGeo = new THREE.CylinderGeometry(1.2, 1.2, 0.18, 16)
    const topMat = new THREE.MeshLambertMaterial({
      color: islandColors[i],
      transparent: true,
      opacity: 0.85,
    })
    const top = new THREE.Mesh(topGeo, topMat)
    top.position.y = 0.05
    islandGroup.add(top)

    // 一棵小树（圆柱 + 圆锥）
    if (i !== 1) {  // 中间岛不放假树，避免视觉拥挤
      const trunkGeo = new THREE.CylinderGeometry(0.04, 0.06, 0.4, 6)
      const trunkMat = new THREE.MeshLambertMaterial({ color: 0x6B5A48 })
      const trunk = new THREE.Mesh(trunkGeo, trunkMat)
      trunk.position.y = 0.35
      islandGroup.add(trunk)

      const leavesGeo = new THREE.ConeGeometry(0.28, 0.55, 6)
      const leavesMat = new THREE.MeshLambertMaterial({
        color: 0x93B58B,
        flatShading: true,
      })
      const leaves = new THREE.Mesh(leavesGeo, leavesMat)
      leaves.position.y = 0.78
      islandGroup.add(leaves)
    }

    const p = islandPositions[i]
    islandGroup.position.set(p.x, p.y, p.z)
    islandGroup.scale.setScalar(p.scale)
    islandGroup.userData = {
      baseY: p.y,
      floatPhase: Math.random() * Math.PI * 2,
      floatAmp: 0.08 + Math.random() * 0.06,
      rotSpeed: 0.02 + Math.random() * 0.02,
    }
    scene.add(islandGroup)
    islands.push(islandGroup)
  }

  // ─── 远景光点（增加景深） ───
  const dustCount = isMobile() ? 40 : 80
  const dustPos = new Float32Array(dustCount * 3)
  const dustColor = new Float32Array(dustCount * 3)
  for (let i = 0; i < dustCount; i++) {
    dustPos[i * 3] = (Math.random() - 0.5) * 35
    dustPos[i * 3 + 1] = Math.random() * 8 + 0.5
    dustPos[i * 3 + 2] = (Math.random() - 0.5) * 30 - 8
    const palette = [[0.91, 0.72, 0.77], [0.66, 0.77, 0.63], [0.98, 0.96, 0.95]]
    const c = palette[Math.floor(Math.random() * palette.length)]
    dustColor[i * 3] = c[0]
    dustColor[i * 3 + 1] = c[1]
    dustColor[i * 3 + 2] = c[2]
  }
  const dustGeo = new THREE.BufferGeometry()
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3))
  dustGeo.setAttribute('color', new THREE.BufferAttribute(dustColor, 3))
  const dustMat = new THREE.PointsMaterial({
    size: 0.12,
    vertexColors: true,
    transparent: true,
    opacity: 0.55,
    sizeAttenuation: true,
    depthWrite: false,
  })
  const dust = new THREE.Points(dustGeo, dustMat)
  scene.add(dust)

  // ─── 鼠标视差 ───
  const mouse = { x: 0, y: 0, tx: 0, ty: 0 }
  const onMouse = (e) => {
    const rect = container.getBoundingClientRect()
    mouse.tx = ((e.clientX - rect.left) / rect.width - 0.5) * 2
    mouse.ty = -((e.clientY - rect.top) / rect.height - 0.5) * 2
  }
  container.addEventListener('mousemove', onMouse, { passive: true })

  // ─── 渲染循环 ───
  const clock = new THREE.Clock()
  let stopRAF = null

  const render = () => {
    const t = clock.getElapsedTime()

    // 海面顶点位移（3 层正弦叠加，柔和）
    const pos = sea.geometry.attributes.position.array
    for (let i = 0; i < pos.length; i += 3) {
      const x = seaPositions[i]
      const z = seaPositions[i + 2]
      const wave =
        Math.sin(x * 0.4 + t * 0.8) * 0.18 +
        Math.sin(z * 0.5 + t * 1.1) * 0.14 +
        Math.sin((x + z) * 0.3 + t * 0.6) * 0.10
      pos[i + 1] = wave
    }
    sea.geometry.attributes.position.needsUpdate = true
    sea.geometry.computeVertexNormals()

    // 浮岛：上下浮动 + 缓慢旋转
    for (const isl of islands) {
      const u = isl.userData
      isl.position.y = u.baseY + Math.sin(t * 0.6 + u.floatPhase) * u.floatAmp
      isl.rotation.y += u.rotSpeed * 0.005
    }

    // 远景光点：缓慢上升
    const dp = dust.geometry.attributes.position.array
    for (let i = 0; i < dp.length; i += 3) {
      dp[i + 1] += 0.006
      if (dp[i + 1] > 8.5) dp[i + 1] = 0.5
    }
    dust.geometry.attributes.position.needsUpdate = true

    // 相机：自动呼吸 + 鼠标视差
    mouse.x += (mouse.tx - mouse.x) * 0.04
    mouse.y += (mouse.ty - mouse.y) * 0.04
    camera.position.x = Math.sin(t * 0.18) * 1.2 + mouse.x * 1.5
    camera.position.y = 4 + Math.sin(t * 0.25) * 0.3 + mouse.y * 0.5
    camera.position.z = 12
    camera.lookAt(0, 1.2, 0)

    renderer.render(scene, camera)
  }
  stopRAF = smartRAF(render)

  // ─── resize ───
  const onResize = () => {
    if (!container) return
    const w = container.clientWidth
    const h = container.clientHeight
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h)
  }
  const ro = new ResizeObserver(onResize)
  ro.observe(container)

  three.value = {
    scene, renderer, camera, clock,
    sea, seaPositions, islands, dust,
    stopRAF, ro, onMouse, container,
    _THREE: THREE,
  }
}

onBeforeUnmount(() => {
  const t = three.value
  if (!t) return
  if (t.stopRAF) t.stopRAF()
  if (t.ro) t.ro.disconnect()
  if (t.container && t.onMouse) {
    t.container.removeEventListener('mousemove', t.onMouse)
  }
  // 释放资源
  if (t.sea) {
    t.sea.geometry.dispose()
    t.sea.material.dispose()
  }
  if (t.islands) {
    t.islands.forEach((g) => {
      g.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose()
        if (obj.material) obj.material.dispose()
      })
    })
  }
  if (t.dust) {
    t.dust.geometry.dispose()
    t.dust.material.dispose()
  }
  if (t.renderer) {
    t.renderer.dispose()
    if (t.renderer.domElement && t.container?.contains(t.renderer.domElement)) {
      t.container.removeChild(t.renderer.domElement)
    }
  }
})
</script>

<template>
  <div
    class="hero-scene"
    :style="{ height }"
    role="img"
    aria-label="浮岛雾海场景"
  >
    <!-- Three.js 容器 -->
    <div
      v-show="showThree"
      ref="containerRef"
      class="hero-scene__canvas-wrap"
    />

    <!-- SVG 降级插画（reduced-motion / 无 WebGL / 低性能） -->
    <div
      v-show="showFallback"
      ref="fallbackRef"
      class="hero-scene__fallback"
    >
      <svg
        viewBox="0 0 800 480"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#FAF8F4" />
            <stop offset="100%" stop-color="#E5E0D5" />
          </linearGradient>
          <radialGradient id="sun" cx="0.7" cy="0.3" r="0.4">
            <stop offset="0%" stop-color="#FFF5E0" stop-opacity="0.8" />
            <stop offset="100%" stop-color="#FFF5E0" stop-opacity="0" />
          </radialGradient>
        </defs>
        <rect width="800" height="480" fill="url(#sky)" />
        <rect width="800" height="480" fill="url(#sun)" />
        <!-- 远岛 -->
        <ellipse cx="180" cy="260" rx="60" ry="14" fill="#C5BCA8" opacity="0.5" />
        <ellipse cx="620" cy="270" rx="80" ry="16" fill="#C5BCA8" opacity="0.5" />
        <!-- 主岛 -->
        <ellipse cx="400" cy="320" rx="120" ry="22" fill="#8B7B5E" opacity="0.6" />
        <ellipse cx="400" cy="310" rx="115" ry="20" fill="#A8C5A0" opacity="0.7" />
        <!-- 树 -->
        <rect x="395" y="270" width="6" height="40" fill="#6B5A48" />
        <polygon points="400,250 380,275 420,275" fill="#93B58B" />
        <polygon points="400,240 385,265 415,265" fill="#93B58B" />
        <!-- 海平线 -->
        <line x1="0" y1="340" x2="800" y2="340" stroke="#A8B8C5" stroke-width="1" opacity="0.4" />
        <!-- 远景波浪 -->
        <path d="M 0 360 Q 100 350 200 360 T 400 360 T 600 360 T 800 360 L 800 480 L 0 480 Z" fill="#A8B8C5" opacity="0.18" />
        <path d="M 0 400 Q 100 390 200 400 T 400 400 T 600 400 T 800 400 L 800 480 L 0 480 Z" fill="#A8B8C5" opacity="0.25" />
        <path d="M 0 440 Q 100 430 200 440 T 400 440 T 600 440 T 800 440 L 800 480 L 0 480 Z" fill="#A8B8C5" opacity="0.32" />
        <!-- 漂浮小点 -->
        <circle cx="100" cy="180" r="3" fill="#E8B8C5" opacity="0.6" />
        <circle cx="240" cy="120" r="2" fill="#A8C5A0" opacity="0.5" />
        <circle cx="540" cy="160" r="2.5" fill="#A8B8C5" opacity="0.55" />
        <circle cx="680" cy="200" r="2" fill="#FAF6F2" opacity="0.7" />
        <circle cx="380" cy="90" r="1.5" fill="#E8B8C5" opacity="0.5" />
      </svg>
    </div>
  </div>
</template>

<style scoped>
.hero-scene {
  position: relative;
  width: 100%;
  border-radius: var(--radius-xl, 32px);
  overflow: hidden;
  background: linear-gradient(180deg, #FAF8F4 0%, #F0EDE5 100%);
}

.hero-scene__canvas-wrap,
.hero-scene__fallback {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero-scene__canvas-wrap :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}

.hero-scene__fallback svg {
  width: 100%;
  height: 100%;
  display: block;
}

/* reduced-motion：SVG 静态插画（无动画） */
@media (prefers-reduced-motion: reduce) {
  .hero-scene__canvas-wrap {
    display: none;
  }
  .hero-scene__fallback {
    display: block;
  }
}

/* 移动端：高度自适应，圆角缩小 */
@media (max-width: 768px) {
  .hero-scene {
    border-radius: var(--radius-lg, 20px);
  }
}
</style>
