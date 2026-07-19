<script setup>
/**
 * FlowerField.vue — Three.js 伪 3D 花田场景
 *
 * 设计：
 * - 用 InstancedMesh 高性能渲染大量花瓣（每朵花 5 片花瓣 + 1 花蕊）
 * - 摄影机斜视角，鼠标移动时轻微跟随 + 自动呼吸摆动
 * - 雾效 + 渐变天空，营造花田深处的氛围
 * - 顶点着色器让花瓣在风中轻摆
 * - 花朵随时间缓缓"绽放"（从地面升起 + 旋转）
 *
 * 治愈系配色：藕粉 #E8B8C5 / 淡黄 #E8D5A8 / 青绿 #A8C5A0 / 雾蓝 #A8B8C5 / 纯白 #FAF6F2
 */
import { ref, onMounted, onBeforeUnmount, shallowRef } from 'vue'

const props = defineProps({
  flowerCount: {
    type: Number,
    default: 60,  // 60 朵花 × 5 瓣 = 300 个实例，性能与视觉的平衡点
  },
  height: {
    type: String,
    default: '420px',
  },
})

const emit = defineEmits(['loaded'])

const containerRef = ref(null)
const isLoading = ref(true)

// shallowRef 避免 Three.js 对象被 Vue 深度代理（性能）
const three = shallowRef({
  scene: null,
  renderer: null,
  camera: null,
  clock: null,
  flowers: null,        // InstancedMesh
  petalGeometry: null,
  petalMaterial: null,
  animationId: null,
  resizeObserver: null,
  mouse: { x: 0, y: 0, tx: 0, ty: 0 },
})

// 治愈系花朵配色（5 种）
const FLOWER_COLORS = [
  0xE8B8C5,  // 藕粉
  0xE8D5A8,  // 淡黄
  0xA8C5A0,  // 青绿
  0xA8B8C5,  // 雾蓝
  0xFAF6F2,  // 纯白
]

// ─── 初始化场景 ───
const initScene = async () => {
  // 动态导入 Three.js（按需加载，减小首屏包）
  const THREE = await import('three')
  // 保存 THREE 引用，动画循环里要用
  three.value._THREE = THREE
  three.value._dummy = new THREE.Object3D()

  const container = containerRef.value
  if (!container) return

  const width = container.clientWidth
  const height = container.clientHeight

  // 场景
  const scene = new THREE.Scene()
  // 治愈系雾色（与背景同色，远处花朵融入雾里）
  scene.background = new THREE.Color(0xF9F6F0)
  scene.fog = new THREE.Fog(0xF9F6F0, 8, 28)

  // 摄影机：斜视角，从花的上方俯瞰花田
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
  camera.position.set(0, 6, 12)
  camera.lookAt(0, 0, 0)

  // 渲染器
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance',
  })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = false  // 性能优先，花田不用阴影
  container.appendChild(renderer.domElement)

  // ─── 光照 ───
  // 主光：暖色环境光（治愈系柔和）
  const ambient = new THREE.AmbientLight(0xFFEEDD, 0.7)
  scene.add(ambient)
  // 方向光：从右上方斜照，模拟午后阳光
  const dirLight = new THREE.DirectionalLight(0xFFF5E0, 0.9)
  dirLight.position.set(5, 10, 6)
  scene.add(dirLight)
  // 补光：从左侧来一点冷色调，增加层次
  const fillLight = new THREE.DirectionalLight(0xC8DCE8, 0.35)
  fillLight.position.set(-6, 4, -3)
  scene.add(fillLight)

  // ─── 花田地面（淡淡的草地色）───
  const groundGeo = new THREE.CircleGeometry(20, 64)
  const groundMat = new THREE.MeshBasicMaterial({
    color: 0xE4E9DC,
    transparent: true,
    opacity: 0.6,
  })
  const ground = new THREE.Mesh(groundGeo, groundMat)
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.05
  scene.add(ground)

  // ─── 花瓣几何体（自定义形状：圆润花瓣）───
  const petalShape = new THREE.Shape()
  petalShape.moveTo(0, 0)
  petalShape.bezierCurveTo(0.15, 0.15, 0.35, 0.5, 0.15, 0.85)
  petalShape.bezierCurveTo(0.05, 1.0, -0.05, 1.0, -0.15, 0.85)
  petalShape.bezierCurveTo(-0.35, 0.5, -0.15, 0.15, 0, 0)

  const petalGeometry = new THREE.ShapeGeometry(petalShape, 12)
  // 把花瓣的"根部"对齐到原点（这样旋转时围绕花蕊）
  petalGeometry.translate(0, 0, 0)
  // 让花瓣稍微立起来（向相机倾斜）
  petalGeometry.rotateX(-Math.PI / 6)

  // ─── 花瓣材质（半透明，渐变效果）───
  const petalMaterial = new THREE.MeshLambertMaterial({
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.95,
    vertexColors: false,
  })

  // ─── 创建 InstancedMesh 渲染所有花瓣 ───
  // 每朵花 5 片花瓣，每片花瓣是一个 instance
  const totalPetals = props.flowerCount * 5
  const flowers = new THREE.InstancedMesh(petalGeometry, petalMaterial, totalPetals)
  // 启用每实例颜色
  flowers.instanceColor = new THREE.InstancedBufferAttribute(
    new Float32Array(totalPetals * 3), 3
  )

  // ─── 生成花朵位置 + 设置每个花瓣的变换矩阵 ───
  const dummy = new THREE.Object3D()
  const color = new THREE.Color()
  const flowerData = []  // 存每朵花的中心位置 + 摆动相位

  let instanceIdx = 0
  for (let i = 0; i < props.flowerCount; i++) {
    // 在圆形花田内随机分布（避免方形阵列的死板）
    const angle = Math.random() * Math.PI * 2
    const radius = Math.sqrt(Math.random()) * 9  // sqrt 让分布均匀
    const fx = Math.cos(angle) * radius
    const fz = Math.sin(angle) * radius
    const fy = 0

    // 花朵高度随机（0.8 ~ 1.3）
    const flowerHeight = 0.8 + Math.random() * 0.5
    // 花朵颜色（5 种治愈色随机）
    const flowerColorIdx = Math.floor(Math.random() * FLOWER_COLORS.length)
    const flowerColor = new THREE.Color(FLOWER_COLORS[flowerColorIdx])
    // 花朵朝向（绕 Y 轴随机旋转）
    const flowerYaw = Math.random() * Math.PI * 2
    // 摆动相位（让每朵花错峰摆动）
    const swayPhase = Math.random() * Math.PI * 2
    const swayAmplitude = 0.04 + Math.random() * 0.04

    flowerData.push({
      x: fx, y: fy, z: fz,
      height: flowerHeight,
      yaw: flowerYaw,
      swayPhase, swayAmplitude,
      bloomDelay: Math.random() * 2.0,  // 错峰绽放
    })

    // 每朵花 5 片花瓣，围绕花蕊均匀分布
    for (let p = 0; p < 5; p++) {
      const petalYaw = flowerYaw + (p / 5) * Math.PI * 2
      dummy.position.set(fx, fy + flowerHeight, fz)
      dummy.rotation.set(0, petalYaw, 0)
      dummy.scale.set(1, 1, 1)
      dummy.updateMatrix()
      flowers.setMatrixAt(instanceIdx, dummy.matrix)

      // 花瓣颜色（轻微变化让花朵更自然）
      const lightness = 0.85 + Math.random() * 0.15
      color.copy(flowerColor).multiplyScalar(lightness)
      flowers.setColorAt(instanceIdx, color)

      instanceIdx++
    }
  }
  flowers.instanceMatrix.needsUpdate = true
  if (flowers.instanceColor) flowers.instanceColor.needsUpdate = true
  flowers.frustumCulled = false  // 避免花田被错误剔除
  scene.add(flowers)

  // ─── 花蕊（小黄点，用 Points 渲染，性能更好）───
  const centerPositions = new Float32Array(props.flowerCount * 3)
  const centerColors = new Float32Array(props.flowerCount * 3)
  for (let i = 0; i < props.flowerCount; i++) {
    const fd = flowerData[i]
    centerPositions[i * 3] = fd.x
    centerPositions[i * 3 + 1] = fd.y + fd.height
    centerPositions[i * 3 + 2] = fd.z
    // 花蕊：暖黄色
    centerColors[i * 3] = 0.95
    centerColors[i * 3 + 1] = 0.78
    centerColors[i * 3 + 2] = 0.45
  }
  const centerGeo = new THREE.BufferGeometry()
  centerGeo.setAttribute('position', new THREE.BufferAttribute(centerPositions, 3))
  centerGeo.setAttribute('color', new THREE.BufferAttribute(centerColors, 3))
  const centerMat = new THREE.PointsMaterial({
    size: 0.18,
    vertexColors: true,
    sizeAttenuation: true,
    transparent: true,
    opacity: 0.95,
  })
  const centers = new THREE.Points(centerGeo, centerMat)
  scene.add(centers)

  // ─── 远处漂浮的"光点"（增加氛围）───
  const dustCount = 80
  const dustPositions = new Float32Array(dustCount * 3)
  for (let i = 0; i < dustCount; i++) {
    dustPositions[i * 3] = (Math.random() - 0.5) * 25
    dustPositions[i * 3 + 1] = Math.random() * 6 + 0.5
    dustPositions[i * 3 + 2] = (Math.random() - 0.5) * 25
  }
  const dustGeo = new THREE.BufferGeometry()
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPositions, 3))
  const dustMat = new THREE.PointsMaterial({
    color: 0xFFF5E0,
    size: 0.08,
    transparent: true,
    opacity: 0.6,
    sizeAttenuation: true,
  })
  const dust = new THREE.Points(dustGeo, dustMat)
  scene.add(dust)

  // ─── 时钟 ───
  const clock = new THREE.Clock()

  // 保存状态
  three.value = {
    scene, renderer, camera, clock,
    flowers, petalGeometry, petalMaterial,
    flowerData, centers, dust,
    animationId: null,
    resizeObserver: null,
    mouse: { x: 0, y: 0, tx: 0, ty: 0 },
  }

  isLoading.value = false
  emit('loaded')
}

// ─── 动画循环 ───
const animate = () => {
  const t = three.value
  if (!t || !t.renderer || !t._THREE) return

  const elapsed = t.clock.getElapsedTime()

  // 摄影机：自动呼吸摆动 + 鼠标跟随
  t.mouse.x += (t.mouse.tx - t.mouse.x) * 0.05
  t.mouse.y += (t.mouse.ty - t.mouse.y) * 0.05
  const breathX = Math.sin(elapsed * 0.3) * 0.8
  const breathY = Math.sin(elapsed * 0.4) * 0.3
  t.camera.position.x = breathX + t.mouse.x * 1.5
  t.camera.position.y = 6 + breathY + t.mouse.y * 0.6
  t.camera.position.z = 12
  t.camera.lookAt(0, 0.5, 0)

  // 花瓣在风中摆动 + 绽放动画
  updatePetals(t, elapsed)

  // 远处光点漂浮
  if (t.dust) {
    const positions = t.dust.geometry.attributes.position.array
    for (let i = 0; i < positions.length; i += 3) {
      positions[i + 1] += 0.005  // 缓缓上升
      if (positions[i + 1] > 6.5) positions[i + 1] = 0.5
    }
    t.dust.geometry.attributes.position.needsUpdate = true
  }

  t.renderer.render(t.scene, t.camera)
  t.animationId = requestAnimationFrame(animate)
}

// 更新所有花瓣的矩阵（风摆动 + 绽放动画）
const updatePetals = (t, elapsed) => {
  if (!t._dummy || !t._THREE) return
  const THREE = t._THREE
  const dummy = t._dummy
  const flowers = t.flowers
  const flowerData = t.flowerData

  let instanceIdx = 0
  for (let i = 0; i < flowerData.length; i++) {
    const fd = flowerData[i]
    // 绽放动画：从地面升起 + 缩放
    const bloomT = Math.max(0, Math.min(1, (elapsed - fd.bloomDelay) / 1.5))
    const bloomEase = bloomT < 0.5 ? 2 * bloomT * bloomT : 1 - Math.pow(-2 * bloomT + 2, 2) / 2
    const currentHeight = fd.height * bloomEase
    const currentScale = 0.3 + 0.7 * bloomEase

    // 风摆动
    const sway = Math.sin(elapsed * 1.2 + fd.swayPhase) * fd.swayAmplitude

    for (let p = 0; p < 5; p++) {
      const petalYaw = fd.yaw + (p / 5) * Math.PI * 2
      dummy.position.set(fd.x, fd.y + currentHeight, fd.z)
      dummy.rotation.set(sway * 0.5, petalYaw + sway * 0.2, sway * 0.3)
      dummy.scale.set(currentScale, currentScale, currentScale)
      dummy.updateMatrix()
      flowers.setMatrixAt(instanceIdx, dummy.matrix)

      // 花蕊位置同步
      if (p === 0 && t.centers) {
        const centerPositions = t.centers.geometry.attributes.position.array
        centerPositions[i * 3] = fd.x
        centerPositions[i * 3 + 1] = fd.y + currentHeight
        centerPositions[i * 3 + 2] = fd.z
      }

      instanceIdx++
    }
  }
  flowers.instanceMatrix.needsUpdate = true
  if (t.centers) t.centers.geometry.attributes.position.needsUpdate = true
}

// ─── 事件处理 ───
const handleMouseMove = (e) => {
  const t = three.value
  if (!t) return
  const rect = containerRef.value.getBoundingClientRect()
  t.mouse.tx = ((e.clientX - rect.left) / rect.width - 0.5) * 2
  t.mouse.ty = -((e.clientY - rect.top) / rect.height - 0.5) * 2
}

const handleResize = () => {
  const t = three.value
  if (!t || !t.renderer || !containerRef.value) return
  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight
  t.camera.aspect = width / height
  t.camera.updateProjectionMatrix()
  t.renderer.setSize(width, height)
}

onMounted(async () => {
  await initScene()
  animate()

  // 监听窗口 + 容器尺寸变化
  if (containerRef.value) {
    const ro = new ResizeObserver(handleResize)
    ro.observe(containerRef.value)
    three.value.resizeObserver = ro
  }
  window.addEventListener('mousemove', handleMouseMove)
})

onBeforeUnmount(() => {
  const t = three.value
  if (!t) return
  if (t.animationId) cancelAnimationFrame(t.animationId)
  if (t.resizeObserver) t.resizeObserver.disconnect()
  window.removeEventListener('mousemove', handleMouseMove)
  // 释放 Three.js 资源
  if (t.flowers) {
    t.flowers.geometry?.dispose()
    t.flowers.material?.dispose()
  }
  if (t.centers) {
    t.centers.geometry?.dispose()
    t.centers.material?.dispose()
  }
  if (t.dust) {
    t.dust.geometry?.dispose()
    t.dust.material?.dispose()
  }
  if (t.renderer) {
    t.renderer.dispose()
    if (t.renderer.domElement && containerRef.value) {
      containerRef.value.removeChild(t.renderer.domElement)
    }
  }
})
</script>

<template>
  <div
    ref="containerRef"
    class="flower-field"
    :style="{ height }"
    role="img"
    aria-label="治愈系 3D 花田场景"
  >
    <!-- 加载占位 -->
    <div v-if="isLoading" class="flower-field__loading">
      <span class="flower-field__loading-icon">🌿</span>
      <span class="flower-field__loading-text">花田正在生长…</span>
    </div>
  </div>
</template>

<style scoped>
.flower-field {
  position: relative;
  width: 100%;
  border-radius: var(--radius-lg, 20px);
  overflow: hidden;
  background: linear-gradient(180deg, #F9F6F0 0%, #E4E9DC 100%);
  cursor: grab;
}

.flower-field__loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-text-muted, #8B7B5E);
  background: linear-gradient(180deg, #F9F6F0 0%, #E4E9DC 100%);
  z-index: 2;
}

.flower-field__loading-icon {
  font-size: 48px;
  animation: breathe 2s ease-in-out infinite;
}

.flower-field__loading-text {
  font-family: var(--font-serif, serif);
  font-size: 14px;
  letter-spacing: 0.1em;
}

@keyframes breathe {
  0%, 100% { transform: scale(1); opacity: 0.7; }
  50% { transform: scale(1.1); opacity: 1; }
}

/* 响应式 */
@media (max-width: 640px) {
  .flower-field {
    border-radius: var(--radius-md, 12px);
  }
}
</style>
