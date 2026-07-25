<script setup>
/**
 * FlowerField.vue — Three.js 3D 花田场景（v2 现代化重构）
 *
 * v2 升级要点（解决"红白机观感"和"交互不明确"两大问题）：
 *   1. 3D 立体花瓣：自定义 BufferGeometry（4×6 顶点网格 + Z 轴弯曲），替代 2D ShapeGeometry
 *   2. PBR 材质：MeshPhysicalMaterial + sheen + clearcoat + envMap 反射
 *   3. 新增花茎：InstancedMesh 圆柱，让花朵有支撑感
 *   4. 阴影：PCFSoftShadowMap，花朵在地面投下柔和阴影
 *   5. 后处理：UnrealBloomPass + OutputPass（花蕊高光柔化）
 *   6. 柔光粒子：sprite 纹理替代方形点
 *   7. 交互：OrbitControls（限制极角，缓慢自动旋转）+ SceneHint + SceneControls
 *   8. 点击：raycaster 拾取 InstancedMesh → 花朵爆裂脉冲 + 花语 tooltip
 *
 * 性能保留：
 *   - InstancedMesh 渲染所有花瓣（60 朵 × 5 瓣 = 300 实例，1 draw call）
 *   - InstancedMesh 渲染所有花蕊 + 花茎（各 60 实例）
 *   - smartRAF 不可见时暂停
 *
 * 4 铁律：shallowRef / smartRAF / onBeforeUnmount 完整释放 / 无音频源
 */
import { ref, onMounted, onBeforeUnmount, shallowRef, watch } from 'vue'
import {
  shouldUseThreeJS,
  isMobile,
  smartRAF,
} from '@/utils/visual'
import {
  createRenderer,
  createEnvironment,
  createPostProcessing,
  createOrbitControls,
  createKeyLight,
  createFillLight,
  createSoftSpriteTexture,
  disposeObject3D,
  disposeRenderer,
} from '@/utils/three-helpers'
import SceneHint from '@/components/SceneHint.vue'
import SceneControls from '@/components/SceneControls.vue'

const props = defineProps({
  flowerCount: {
    type: Number,
    default: 60,
  },
  height: {
    type: String,
    default: '420px',
  },
})
const emit = defineEmits(['loaded'])

// 5 种治愈系花色 + 花语
const FLOWER_KINDS = [
  { hex: 0xE8B8C5, name: '温柔的陪伴' },
  { hex: 0xE8D5A8, name: '阳光的心意' },
  { hex: 0xA8C5A0, name: '宁静的生长' },
  { hex: 0xA8B8C5, name: '深沉的思念' },
  { hex: 0xFAF6F2, name: '纯粹的可能' },
]

const containerRef = ref(null)
const isLoading = ref(true)
const showHint = ref(true)
const autoRotate = ref(true)
// 选中的花语 tooltip
const selectedFlower = ref(null)
let tooltipTimer = null

const three = shallowRef(null)

// ─── 自定义立体花瓣 BufferGeometry ───
// 水滴形花瓣：根部窄（接花蕊）→ 中部最宽 → 尖端收窄
// 沿 +Y 方向生长，Z 方向有柔和弧度（花瓣向前凸）
function createPetalGeometry(THREE, mobile = false) {
  // 移动端降低网格细分（顶点数减少约 50%）
  const widthSegs = mobile ? 4 : 5
  const heightSegs = mobile ? 6 : 8
  const maxWidth = 0.45
  const height = 1.0
  const vertices = []
  const uvs = []
  const indices = []

  for (let iy = 0; iy <= heightSegs; iy++) {
    const v = iy / heightSegs
    const y = v * height
    // 水滴形宽度曲线：根部 0.2 → 中部 1.0 → 尖端 0.1
    const widthFactor = 0.2 + Math.sin(v * Math.PI) * 0.8 + (1 - v) * 0.0
    const widthAtY = maxWidth * Math.max(0.05, widthFactor)
    // Z 方向弧度：中部凸起，根部和尖端平
    const zBulge = Math.sin(v * Math.PI) * 0.18
    for (let ix = 0; ix <= widthSegs; ix++) {
      const u = ix / widthSegs
      const x = (u - 0.5) * widthAtY
      // 中间凸起多，边缘凸起少（形成弧面）
      const edgeFactor = 1 - Math.abs(u - 0.5) * 1.8
      const z = zBulge * Math.max(0, edgeFactor)
      vertices.push(x, y, z)
      uvs.push(u, v)
    }
  }
  for (let iy = 0; iy < heightSegs; iy++) {
    for (let ix = 0; ix < widthSegs; ix++) {
      const a = iy * (widthSegs + 1) + ix
      const b = a + 1
      const c = a + (widthSegs + 1)
      const d = c + 1
      indices.push(a, c, b)
      indices.push(b, c, d)
    }
  }
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2))
  geo.setIndex(indices)
  geo.computeVertexNormals()
  return geo
}

const initScene = async () => {
  const THREE = await import('three')
  const container = containerRef.value
  if (!container) return
  const width = container.clientWidth
  const height = container.clientHeight
  const mobile = isMobile()

  // ─── 场景 ───
  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0xE8DCC8)
  scene.fog = new THREE.Fog(0xE8DCC8, 10, 32)

  // ─── 相机 ───
  const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100)
  const INITIAL_CAM_POS = new THREE.Vector3(0, 5.5, 11)
  const INITIAL_CAM_TARGET = new THREE.Vector3(0, 0.6, 0)
  camera.position.copy(INITIAL_CAM_POS)
  camera.lookAt(INITIAL_CAM_TARGET)

  // ─── 渲染器（PBR + 阴影） ───
  const canvas = document.createElement('canvas')
  container.appendChild(canvas)
  const renderer = createRenderer(canvas, {
    dpr: mobile ? 1.5 : 2,
    shadows: true,
    toneMappingExposure: 0.92,
  })
  renderer.setSize(width, height)

  // ─── 环境贴图 ───
  const { envMap, pmrem } = createEnvironment(renderer, mobile ? 128 : 256)
  scene.environment = envMap

  // ─── 后处理 ───
  const composer = createPostProcessing(scene, camera, renderer, {
    strength: mobile ? 0.18 : 0.25,
    radius: 0.5,
    threshold: 0.88,
  })

  // ─── OrbitControls ───
  const controls = createOrbitControls(camera, renderer.domElement, {
    minDistance: 5,
    maxDistance: 18,
    minPolarAngle: 0.25,
    maxPolarAngle: Math.PI / 2 - 0.05,
    autoRotate: autoRotate.value,
    autoRotateSpeed: 0.3,
    enablePan: false,
    rotateSpeed: 0.6,
  })
  controls.target.copy(INITIAL_CAM_TARGET)

  // ─── 光照 ───
  const keyLight = createKeyLight({
    position: [6, 12, 5],
    intensity: 1.3,
    color: 0xfff4e0,
    shadow: {
      mapSize: mobile ? 1024 : 2048,
      camera: { near: 0.5, far: 40, left: -15, right: 15, top: 15, bottom: -15 },
      bias: -0.0005,
      radius: 4,
    },
  })
  scene.add(keyLight)
  const fillLight = createFillLight({ intensity: 0.4 })
  scene.add(fillLight)

  // ─── 地面（草地色，receiveShadow） ───
  // 移动端降低圆形分段（64 → 32）
  const groundGeo = new THREE.CircleGeometry(22, mobile ? 32 : 64)
  const groundMat = new THREE.MeshStandardMaterial({
    color: 0xE4E9DC,
    roughness: 0.92,
    metalness: 0.0,
    envMap,
    envMapIntensity: 0.4,
  })
  const ground = new THREE.Mesh(groundGeo, groundMat)
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.02
  ground.receiveShadow = true
  scene.add(ground)

  // ─── 花瓣 InstancedMesh（立体 PBR 花瓣） ───
  const petalGeo = createPetalGeometry(THREE, mobile)
  const petalMat = new THREE.MeshPhysicalMaterial({
    roughness: 0.45,
    metalness: 0.0,
    sheen: 0.7,
    sheenColor: new THREE.Color(0xffffff),
    sheenRoughness: 0.5,
    clearcoat: 0.2,
    clearcoatRoughness: 0.4,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.97,
    envMap,
    envMapIntensity: 0.9,
  })

  const totalPetals = props.flowerCount * 5
  const flowers = new THREE.InstancedMesh(petalGeo, petalMat, totalPetals)
  flowers.castShadow = true
  flowers.instanceColor = new THREE.InstancedBufferAttribute(
    new Float32Array(totalPetals * 3), 3,
  )

  // ─── 花蕊 InstancedMesh（小球，emissive 黄色，Bloom 高亮） ───
  // 移动端降低 icosahedron 细分（2 → 1，顶点数减少 75%）
  const centerGeo = new THREE.IcosahedronGeometry(0.11, mobile ? 1 : 2)
  const centerMat = new THREE.MeshStandardMaterial({
    color: 0xF5C870,
    roughness: 0.4,
    metalness: 0.0,
    emissive: 0xF5A830,
    emissiveIntensity: 0.7,
    envMap,
    envMapIntensity: 0.9,
  })
  const centers = new THREE.InstancedMesh(centerGeo, centerMat, props.flowerCount)
  centers.castShadow = true

  // ─── 花茎 InstancedMesh（细圆柱） ───
  // 移动端降低圆柱段数（6 → 5）
  const stemGeo = new THREE.CylinderGeometry(0.025, 0.03, 1.0, mobile ? 5 : 6)
  const stemMat = new THREE.MeshStandardMaterial({
    color: 0x7A9B68,
    roughness: 0.85,
    metalness: 0.0,
    envMap,
    envMapIntensity: 0.5,
  })
  const stems = new THREE.InstancedMesh(stemGeo, stemMat, props.flowerCount)
  stems.castShadow = true

  // ─── 生成花朵数据 + 初始化实例矩阵 ───
  const dummy = new THREE.Object3D()
  const color = new THREE.Color()
  const flowerData = []
  // 花瓣倾斜角度（绕局部 X 轴，负值 = 向外张开，形成杯状）
  // -55 度 ≈ -Math.PI / 3.27，花瓣从中心向上+向外张开
  const petalTilt = -Math.PI / 3.2
  const petalEuler = new THREE.Euler(petalTilt, 0, 0, 'YXZ')
  const petalQuat = new THREE.Quaternion().setFromEuler(petalEuler)

  let instanceIdx = 0
  for (let i = 0; i < props.flowerCount; i++) {
    const angle = Math.random() * Math.PI * 2
    const radius = Math.sqrt(Math.random()) * 9
    const fx = Math.cos(angle) * radius
    const fz = Math.sin(angle) * radius
    const fy = 0
    const flowerHeight = 0.9 + Math.random() * 0.5
    const kind = FLOWER_KINDS[Math.floor(Math.random() * FLOWER_KINDS.length)]
    const flowerColor = new THREE.Color(kind.hex)
    const flowerYaw = Math.random() * Math.PI * 2
    const swayPhase = Math.random() * Math.PI * 2
    const swayAmplitude = 0.05 + Math.random() * 0.05

    flowerData.push({
      x: fx, y: fy, z: fz,
      height: flowerHeight,
      yaw: flowerYaw,
      swayPhase, swayAmplitude,
      bloomDelay: Math.random() * 2.0,
      kind,
      burstEnd: 0,  // 爆裂动画结束时间戳（秒）
    })

    // 花朵中心 Y 坐标（花瓣根部 + 花蕊位置）
    const flowerCenterY = fy + flowerHeight

    // 5 片花瓣（杯状分布：绕 Y 轴均匀分布 + 绕局部 X 轴倾斜向外张开）
    for (let p = 0; p < 5; p++) {
      const petalYaw = flowerYaw + (p / 5) * Math.PI * 2
      dummy.position.set(fx, flowerCenterY, fz)
      // 用 Quaternion 组合：先绕 Y 轴分布，再绕局部 X 轴倾斜
      const yawQuat = new THREE.Quaternion().setFromAxisAngle(
        new THREE.Vector3(0, 1, 0), petalYaw,
      )
      dummy.quaternion.copy(yawQuat).multiply(petalQuat)
      dummy.scale.set(0.42, 0.42, 0.42)
      dummy.updateMatrix()
      flowers.setMatrixAt(instanceIdx, dummy.matrix)

      const lightness = 0.85 + Math.random() * 0.15
      color.copy(flowerColor).multiplyScalar(lightness)
      flowers.setColorAt(instanceIdx, color)

      instanceIdx++
    }

    // 花蕊（在花朵中心，稍微低于花瓣顶部）
    dummy.position.set(fx, flowerCenterY + 0.04, fz)
    dummy.quaternion.identity()
    dummy.scale.set(1, 1, 1)
    dummy.updateMatrix()
    centers.setMatrixAt(i, dummy.matrix)

    // 花茎（从地面到花朵底部，长度=flowerHeight - 0.1）
    const stemLen = flowerHeight - 0.1
    dummy.position.set(fx, fy + stemLen * 0.5, fz)
    dummy.quaternion.identity()
    dummy.scale.set(1, stemLen, 1)
    dummy.updateMatrix()
    stems.setMatrixAt(i, dummy.matrix)
  }
  flowers.instanceMatrix.needsUpdate = true
  if (flowers.instanceColor) flowers.instanceColor.needsUpdate = true
  flowers.frustumCulled = false
  centers.instanceMatrix.needsUpdate = true
  centers.frustumCulled = false
  stems.instanceMatrix.needsUpdate = true
  stems.frustumCulled = false
  scene.add(flowers, centers, stems)

  // ─── 漂浮柔光粒子 ───
  const dustCount = mobile ? 50 : 100
  const dustPos = new Float32Array(dustCount * 3)
  const dustColor = new Float32Array(dustCount * 3)
  for (let i = 0; i < dustCount; i++) {
    dustPos[i * 3] = (Math.random() - 0.5) * 25
    dustPos[i * 3 + 1] = Math.random() * 6 + 0.5
    dustPos[i * 3 + 2] = (Math.random() - 0.5) * 25
    const k = FLOWER_KINDS[Math.floor(Math.random() * FLOWER_KINDS.length)]
    const cc = new THREE.Color(k.hex)
    dustColor[i * 3] = cc.r
    dustColor[i * 3 + 1] = cc.g
    dustColor[i * 3 + 2] = cc.b
  }
  const dustGeo = new THREE.BufferGeometry()
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3))
  dustGeo.setAttribute('color', new THREE.BufferAttribute(dustColor, 3))
  const spriteTex = createSoftSpriteTexture(128, '#ffffff')
  const dustMat = new THREE.PointsMaterial({
    size: 0.18,
    map: spriteTex,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    sizeAttenuation: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })
  const dust = new THREE.Points(dustGeo, dustMat)
  scene.add(dust)

  // ─── raycaster 拾取花朵 ───
  const raycaster = new THREE.Raycaster()
  const pointer = new THREE.Vector2()
  let t_flying = false  // 飞行动画标志（闭包内，需在 onPointerDown 之前声明）
  const clock = new THREE.Clock()

  const onPointerDown = (e) => {
    if (t_flying) return
    const rect = renderer.domElement.getBoundingClientRect()
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1
    raycaster.setFromCamera(pointer, camera)
    const hits = raycaster.intersectObject(flowers, false)
    if (hits.length > 0) {
      const instanceId = hits[0].instanceId
      const flowerIdx = Math.floor(instanceId / 5)
      const fd = flowerData[flowerIdx]
      // 触发爆裂动画（1.5s）
      fd.burstEnd = clock.getElapsedTime() + 1.5
      // 显示花语 tooltip（屏幕坐标）
      const v = new THREE.Vector3(fd.x, fd.y + fd.height + 0.5, fd.z)
      v.project(camera)
      const sx = (v.x * 0.5 + 0.5) * rect.width
      const sy = (-v.y * 0.5 + 0.5) * rect.height
      selectedFlower.value = { name: fd.kind.name, x: sx, y: sy }
      if (tooltipTimer) clearTimeout(tooltipTimer)
      tooltipTimer = setTimeout(() => {
        selectedFlower.value = null
      }, 3500)
    }
  }
  renderer.domElement.addEventListener('pointerdown', onPointerDown)

  // ─── 用户首次交互：关闭 hint ───
  const onFirstInteract = () => {
    showHint.value = false
  }
  renderer.domElement.addEventListener('pointerdown', onFirstInteract, { once: true })
  renderer.domElement.addEventListener('wheel', onFirstInteract, { once: true })

  // ─── 渲染循环 ───
  // 预计算复用对象（避免每帧 new）
  const yAxis = new THREE.Vector3(0, 1, 0)
  const swayAxisX = new THREE.Vector3(1, 0, 0)
  const tmpYawQuat = new THREE.Quaternion()
  const tmpSwayQuat = new THREE.Quaternion()

  const render = () => {
    const elapsed = clock.getElapsedTime()

    // 更新花瓣/花蕊/花茎矩阵（绽放 + 风摆 + 爆裂脉冲）
    let instIdx = 0
    for (let i = 0; i < flowerData.length; i++) {
      const fd = flowerData[i]
      // 绽放动画
      const bloomT = Math.max(0, Math.min(1, (elapsed - fd.bloomDelay) / 1.5))
      const bloomEase = bloomT < 0.5 ? 2 * bloomT * bloomT : 1 - Math.pow(-2 * bloomT + 2, 2) / 2
      const currentHeight = fd.height * bloomEase
      let currentScale = 0.3 + 0.7 * bloomEase

      // 爆裂动画（点击后 1.5s 内放大脉冲）
      if (elapsed < fd.burstEnd) {
        const burstT = 1 - (fd.burstEnd - elapsed) / 1.5
        currentScale += Math.sin(burstT * Math.PI) * 0.45
      }

      // 风摆动
      const sway = Math.sin(elapsed * 1.2 + fd.swayPhase) * fd.swayAmplitude
      // 花瓣最终 scale = bloomScale × 0.42（0.42 是花瓣基础大小）
      const petalScale = currentScale * 0.42
      const flowerCenterY = fd.y + currentHeight

      // 5 片花瓣（杯状分布 + 风摆）
      for (let p = 0; p < 5; p++) {
        const petalYaw = fd.yaw + (p / 5) * Math.PI * 2
        dummy.position.set(fd.x, flowerCenterY, fd.z)
        // Quaternion 组合：yaw 分布 × tilt 倾斜 × sway 风摆
        tmpYawQuat.setFromAxisAngle(yAxis, petalYaw + sway * 0.2)
        tmpSwayQuat.setFromAxisAngle(swayAxisX, sway * 0.4)
        dummy.quaternion.copy(tmpYawQuat).multiply(petalQuat).multiply(tmpSwayQuat)
        dummy.scale.set(petalScale, petalScale, petalScale)
        dummy.updateMatrix()
        flowers.setMatrixAt(instIdx, dummy.matrix)
        instIdx++
      }

      // 花蕊（在花朵中心，稍微高于花瓣根部）
      dummy.position.set(fd.x, flowerCenterY + 0.04, fd.z)
      dummy.quaternion.identity()
      dummy.scale.set(currentScale, currentScale, currentScale)
      dummy.updateMatrix()
      centers.setMatrixAt(i, dummy.matrix)

      // 花茎（从地面到花朵底部，长度=currentHeight - 0.1）
      const stemLen = Math.max(0.1, currentHeight - 0.1)
      dummy.position.set(fd.x, fd.y + stemLen * 0.5, fd.z)
      // 花茎随风摆动（绕 X 轴轻微倾斜）
      dummy.quaternion.setFromAxisAngle(swayAxisX, sway * 0.3)
      dummy.scale.set(1, stemLen, 1)
      dummy.updateMatrix()
      stems.setMatrixAt(i, dummy.matrix)
    }
    flowers.instanceMatrix.needsUpdate = true
    centers.instanceMatrix.needsUpdate = true
    stems.instanceMatrix.needsUpdate = true

    // 漂浮光点
    const dp = dust.geometry.attributes.position.array
    for (let i = 0; i < dp.length; i += 3) {
      dp[i + 1] += 0.004
      dp[i] += Math.sin(elapsed * 0.3 + i) * 0.0015
      if (dp[i + 1] > 6.5) {
        dp[i + 1] = 0.5
        dp[i] = (Math.random() - 0.5) * 25
        dp[i + 2] = (Math.random() - 0.5) * 25
      }
    }
    dust.geometry.attributes.position.needsUpdate = true

    controls.update()
    composer.render()
  }
  const stopRAF = smartRAF(render)

  // ─── resize ───
  const onResize = () => {
    if (!container) return
    const w = container.clientWidth
    const h = container.clientHeight
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h)
    composer.setSize(w, h)
  }
  const ro = new ResizeObserver(onResize)
  ro.observe(container)

  three.value = {
    scene, renderer, camera, composer, controls,
    flowers, centers, stems, dust, spriteTex,
    petalGeo, petalMat, centerGeo, centerMat, stemGeo, stemMat,
    flowerData, dummy,
    envMap, pmrem,
    stopRAF, ro,
    onPointerDown, onFirstInteract,
    container, _THREE: THREE,
    _flying: false,
    // 暴露闭包变量给外部 onResetView 使用
    _getFlying: () => t_flying,
    _setFlying: (v) => { t_flying = v },
  }

  isLoading.value = false
  emit('loaded')
}

// SceneControls 通过 v-model 改 autoRotate，同步到 controls
watch(autoRotate, (v) => {
  const t = three.value
  if (t && t.controls && !t._getFlying()) t.controls.autoRotate = v
})

// 重置视角（外部触发）
const onResetView = () => {
  const t = three.value
  if (!t) return
  const { controls, camera, _THREE } = t
  if (!controls || !camera) return
  t._setFlying(true)
  controls.autoRotate = false
  selectedFlower.value = null
  const INITIAL_CAM_POS = new _THREE.Vector3(0, 5.5, 11)
  const INITIAL_CAM_TARGET = new _THREE.Vector3(0, 0.6, 0)
  const startPos = camera.position.clone()
  const startTarget = controls.target.clone()
  const duration = 1200
  const t0 = performance.now()
  const step = () => {
    const elapsed = performance.now() - t0
    const k = Math.min(1, elapsed / duration)
    const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2
    camera.position.lerpVectors(startPos, INITIAL_CAM_POS, e)
    controls.target.lerpVectors(startTarget, INITIAL_CAM_TARGET, e)
    controls.update()
    if (k < 1) {
      requestAnimationFrame(step)
    } else {
      t._setFlying(false)
      controls.autoRotate = autoRotate.value
    }
  }
  step()
}

onMounted(async () => {
  if (!shouldUseThreeJS() || !containerRef.value) {
    isLoading.value = false
    return
  }
  try {
    await initScene()
  } catch (e) {
    console.warn('[FlowerField] init failed', e)
    isLoading.value = false
  }
})

onBeforeUnmount(() => {
  const t = three.value
  if (!t) return
  if (t.stopRAF) t.stopRAF()
  if (t.ro) t.ro.disconnect()
  if (t.onPointerDown && t.renderer?.domElement) {
    t.renderer.domElement.removeEventListener('pointerdown', t.onPointerDown)
  }
  if (t.onFirstInteract && t.renderer?.domElement) {
    t.renderer.domElement.removeEventListener('pointerdown', t.onFirstInteract)
    t.renderer.domElement.removeEventListener('wheel', t.onFirstInteract)
  }
  if (tooltipTimer) clearTimeout(tooltipTimer)

  disposeObject3D(t.scene)
  if (t.spriteTex) t.spriteTex.dispose()
  disposeRenderer(t.renderer, t.composer, t.pmrem, t.envMap)

  if (t.renderer?.domElement && t.container?.contains(t.renderer.domElement)) {
    t.container.removeChild(t.renderer.domElement)
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

    <!-- 交互指引 -->
    <SceneHint
      v-if="!isLoading && showHint"
      v-model:visible="showHint"
      text="拖拽旋转 · 滚轮缩放 · 点击花朵看花语"
      gesture="drag-rotate-zoom"
      :auto-hide="6500"
    />

    <!-- 视角控制工具栏 -->
    <SceneControls
      v-if="!isLoading"
      v-model="autoRotate"
      position="bottom-right"
      @reset="onResetView"
    />

    <!-- 花语 tooltip -->
    <transition name="flower-tip">
      <div
        v-if="selectedFlower"
        class="flower-tip"
        :style="{ left: selectedFlower.x + 'px', top: selectedFlower.y + 'px' }"
      >
        <span class="flower-tip__text">{{ selectedFlower.name }}</span>
      </div>
    </transition>
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

.flower-field:active {
  cursor: grabbing;
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
  animation: ff-breathe 2s ease-in-out infinite;
}

.flower-field__loading-text {
  font-family: var(--font-serif, serif);
  font-size: 14px;
  letter-spacing: 0.1em;
}

@keyframes ff-breathe {
  0%, 100% { transform: scale(1); opacity: 0.7; }
  50% { transform: scale(1.1); opacity: 1; }
}

/* 花语 tooltip */
.flower-tip {
  position: absolute;
  transform: translate(-50%, -100%);
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  box-shadow: 0 8px 24px rgba(74, 68, 56, 0.15),
              inset 0 1px 0 rgba(255, 255, 255, 0.9);
  pointer-events: none;
  z-index: 7;
  white-space: nowrap;
}

.flower-tip__text {
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-primary, #3D3327);
  letter-spacing: 0.08em;
}

.flower-tip::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid rgba(255, 255, 255, 0.85);
}

.flower-tip-enter-active,
.flower-tip-leave-active {
  transition: opacity 0.4s var(--ease-apple, cubic-bezier(0.16, 1, 0.3, 1)),
              transform 0.4s var(--ease-apple, cubic-bezier(0.16, 1, 0.3, 1));
}
.flower-tip-enter-from {
  opacity: 0;
  transform: translate(-50%, -90%);
}
.flower-tip-leave-to {
  opacity: 0;
  transform: translate(-50%, -110%);
}

/* 响应式 */
@media (max-width: 768px) {
  .flower-field {
    border-radius: var(--radius-md, 12px);
  }
  .flower-tip {
    padding: 8px 14px;
  }
  .flower-tip__text {
    font-size: 12px;
  }
  .flower-field__loading-icon {
    font-size: 36px;
  }
  .flower-field__loading-text {
    font-size: 13px;
  }
}
</style>
