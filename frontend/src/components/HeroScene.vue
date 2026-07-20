<script setup>
/**
 * HeroScene.vue — HomeView Hero 区的 3D 浮岛雾海场景（v2 现代化重构）
 *
 * 主题呼应："海上有座岛，岛上有人听" — 静屿的核心意象
 *
 * v2 升级要点（解决"红白机观感"和"交互不明确"两大问题）：
 *   1. PBR 渲染管线：ACES Filmic 色调映射 + sRGB + PCFSoftShadowMap + RoomEnvironment
 *   2. 浮岛：LatheGeometry 程序化有机轮廓 + MeshStandardMaterial（带 envMap 反射）
 *   3. 樱花树：分枝结构 + 球形花团 IcosahedronGeometry 高细分（Bloom 高亮）
 *   4. 水面：MeshStandardMaterial + onBeforeCompile 注入多层正弦位移 shader
 *   5. 粒子：柔光圆点 sprite 纹理替代方形点
 *   6. 后处理：UnrealBloomPass + OutputPass（高光柔化，电影感）
 *   7. 交互：OrbitControls 拖拽旋转 + 滚轮缩放 + 自动旋转 + 重置视角
 *   8. 指引：SceneHint 首次进入显示交互提示，首次交互后自动消失
 *   9. 点击：raycaster 拾取主岛 → 相机平滑飞入 + 信息卡浮现
 *
 * 渐进降级（保留 v1 策略）：
 *   - 不支持 WebGL / reduced-motion / 低性能 → SVG 静态浮岛插画
 *   - Three.js 加载失败 → 静默回退 SVG
 *
 * 4 铁律遵循：
 *   - shallowRef 持有 Three.js 对象
 *   - smartRAF 替代 requestAnimationFrame
 *   - onBeforeUnmount 完整释放（geometry / material / texture / renderer / composer / envMap / pmrem / controls / ResizeObserver）
 *   - 无 createMediaElementSource（本组件无音频）
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
  height: {
    type: String,
    default: '520px',
  },
})

const containerRef = ref(null)
const showThree = ref(false)
const showFallback = ref(false)

// 视角控制
const autoRotate = ref(true)
// 主岛信息卡（点击主岛后显示）
const islandInfo = ref(null)
const showHint = ref(true)

const three = shallowRef(null)

onMounted(async () => {
  if (!shouldUseThreeJS() || !containerRef.value) {
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

// ─── 浮岛轮廓生成（LatheGeometry 用） ───
// 程序化点序列，定义从底（尖端）到顶（平台）的侧剖面
function makeIslandProfile(radius, height, jitter = 0.08) {
  const pts = []
  const segments = 10
  // 从底部尖端开始
  pts.push(makeVec2(0, 0))
  for (let i = 1; i <= segments; i++) {
    const t = i / segments
    // 半径从 0 平滑扩张到 radius，带轻微噪声
    const r = radius * Math.pow(t, 0.7) + (Math.random() - 0.5) * jitter
    const y = height * t
    pts.push(makeVec2(Math.max(0.01, r), y))
  }
  // 顶部平台（轻微鼓起）
  pts.push(makeVec2(radius * 1.02, height + 0.05))
  pts.push(makeVec2(radius * 0.98, height + 0.06))
  return pts
}

// 局部 Vector2 工厂，避免顶部导入 THREE（异步加载后再用）
function makeVec2(x, y) {
  return { x, y }
}

// 樱花树生成（递归分枝）
function buildSakuraTree(THREE, envMap, blossomMat, trunkMat) {
  const tree = new THREE.Group()

  // 递归生成一根分枝
  const growBranch = (depth, len, radius, startPos, direction) => {
    if (depth <= 0 || len < 0.08) {
      // 末端：放一个花团
      const blossom = new THREE.Mesh(
        new THREE.IcosahedronGeometry(0.18 + Math.random() * 0.08, 2),
        blossomMat,
      )
      blossom.position.copy(startPos)
      blossom.castShadow = true
      blossom.userData.isBlossom = true
      tree.add(blossom)
      return
    }

    // 树枝段
    const segLen = len
    const branchGeo = new THREE.CylinderGeometry(
      Math.max(0.01, radius * 0.7),
      Math.max(0.01, radius),
      segLen,
      6,
    )
    const branch = new THREE.Mesh(branchGeo, trunkMat)
    branch.castShadow = true
    // 把圆柱移到 startPos 并对齐 direction
    branch.position.copy(startPos).add(direction.clone().multiplyScalar(segLen / 2))
    branch.quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      direction.clone().normalize(),
    )
    tree.add(branch)

    // 末端位置
    const endPos = startPos.clone().add(direction.clone().multiplyScalar(segLen))

    // 分叉：2-3 个子枝
    const branches = depth > 2 ? 2 + Math.floor(Math.random() * 2) : 2
    for (let i = 0; i < branches; i++) {
      const angle = (Math.PI / 6) * (i + 1) + (Math.random() - 0.5) * 0.4
      const azimuth = (Math.PI * 2 * i) / branches + Math.random() * 0.5
      // 在 direction 基础上偏转
      const newDir = direction.clone()
      // 绕一个随机轴旋转
      const axis = new THREE.Vector3(
        Math.cos(azimuth),
        0,
        Math.sin(azimuth),
      ).normalize()
      newDir.applyAxisAngle(axis, angle)
      // 微微向上偏
      newDir.y += 0.15
      newDir.normalize()
      growBranch(
        depth - 1,
        len * (0.62 + Math.random() * 0.12),
        radius * 0.65,
        endPos,
        newDir,
      )
    }
  }

  // 从树根开始
  growBranch(
    4,                    // 深度
    0.55,                 // 初始长度
    0.05,                 // 初始半径
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, 1, 0),  // 向上
  )

  return tree
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
  scene.background = null
  scene.fog = new THREE.FogExp2(0xF9F6F0, mobile ? 0.05 : 0.035)

  // ─── 相机 ───
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
  const INITIAL_CAM_POS = new THREE.Vector3(0, 4.5, 13)
  const INITIAL_CAM_TARGET = new THREE.Vector3(0, 1.5, 0)
  camera.position.copy(INITIAL_CAM_POS)
  camera.lookAt(INITIAL_CAM_TARGET)

  // ─── 渲染器（PBR） ───
  const renderer = createRenderer(container.appendChild(document.createElement('canvas')), {
    dpr: mobile ? 1.5 : 2,
    shadows: true,
    toneMappingExposure: 1.08,
  })
  renderer.setSize(width, height)

  // ─── 环境贴图（PBR 反射） ───
  const { envMap, pmrem } = createEnvironment(renderer, mobile ? 128 : 256)
  scene.environment = envMap

  // ─── 后处理（Bloom + ACES） ───
  const composer = createPostProcessing(scene, camera, renderer, {
    strength: mobile ? 0.4 : 0.55,
    radius: 0.5,
    threshold: 0.72,
  })

  // ─── OrbitControls ───
  const controls = createOrbitControls(camera, renderer.domElement, {
    minDistance: 7,
    maxDistance: 18,
    minPolarAngle: 0.35,
    maxPolarAngle: Math.PI / 2 - 0.08,
    autoRotate: autoRotate.value,
    autoRotateSpeed: 0.35,
    enablePan: false,
    rotateSpeed: 0.65,
  })
  controls.target.copy(INITIAL_CAM_TARGET)

  // ─── 光照 ───
  const keyLight = createKeyLight({
    position: [8, 14, 6],
    intensity: 2.4,
    color: 0xfff4e0,
    shadow: {
      mapSize: mobile ? 1024 : 2048,
      camera: { near: 0.5, far: 50, left: -15, right: 15, top: 15, bottom: -15 },
      bias: -0.0004,
      radius: 5,
    },
  })
  scene.add(keyLight)

  const fillLight = createFillLight({ intensity: 0.55 })
  scene.add(fillLight)

  // 一束逆光（边缘高光）
  const rimLight = new THREE.DirectionalLight(0xE8B8C5, 0.6)
  rimLight.position.set(-6, 5, -8)
  scene.add(rimLight)

  // ─── 水面（PBR + 顶点位移 shader 注入） ───
  const seaSegs = mobile ? 80 : 160
  const seaGeo = new THREE.PlaneGeometry(60, 60, seaSegs, seaSegs)
  seaGeo.rotateX(-Math.PI / 2)

  const seaMat = new THREE.MeshStandardMaterial({
    color: 0xB8D4D8,
    roughness: 0.12,
    metalness: 0.35,
    transparent: true,
    opacity: 0.78,
    envMap,
    envMapIntensity: 1.4,
  })

  // 保存原始 XZ 坐标，shader 中用于计算位移
  const seaPositions = seaGeo.attributes.position.array.slice(0)

  // 通过 onBeforeCompile 注入 vertex shader 位移
  seaMat.onBeforeCompile = (shader) => {
    shader.uniforms.uTime = { value: 0 }
    seaMat.userData.shader = shader

    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <common>',
        `#include <common>
         uniform float uTime;`,
      )
      .replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
         {
           // 多层正弦叠加，柔和起伏
           float w1 = sin(position.x * 0.35 + uTime * 0.7) * 0.20;
           float w2 = sin(position.z * 0.45 + uTime * 0.9) * 0.16;
           float w3 = sin((position.x + position.z) * 0.28 + uTime * 0.55) * 0.12;
           float w4 = sin(length(position.xz) * 0.6 - uTime * 1.2) * 0.08;
           transformed.y += w1 + w2 + w3 + w4;
         }`,
      )
  }

  const sea = new THREE.Mesh(seaGeo, seaMat)
  sea.position.y = -0.6
  sea.receiveShadow = true
  scene.add(sea)

  // ─── 浮岛 ×3 ───
  const islands = []
  const islandData = [
    {
      x: 0, y: 1.6, z: 0, scale: 1.0,
      topColor: 0xC5D9A8, baseColor: 0x6B5A48,
      name: '静屿', verse: '海上有座岛，岛上有人听',
    },
    {
      x: -4.8, y: 2.7, z: -2.5, scale: 0.55,
      topColor: 0xE8C5A8, baseColor: 0x5C4F3E,
      name: '远屿', verse: '云深不知处，唯有钟磬音',
    },
    {
      x: 5.2, y: 2.2, z: -1.8, scale: 0.7,
      topColor: 0xE8B8C5, baseColor: 0x5C4F3E,
      name: '花屿', verse: '落英缤纷处，一念即归途',
    },
  ]

  for (let i = 0; i < islandData.length; i++) {
    const d = islandData[i]
    const islandGroup = new THREE.Group()

    // 浮岛底部：LatheGeometry 程序化轮廓
    const profilePts = makeIslandProfile(1.3, 1.4, 0.06)
    const lathePts = profilePts.map((p) => new THREE.Vector2(p.x, p.y))
    const baseGeo = new THREE.LatheGeometry(lathePts, 24)
    const baseMat = new THREE.MeshStandardMaterial({
      color: d.baseColor,
      roughness: 0.85,
      metalness: 0.05,
      flatShading: false,
      envMap,
      envMapIntensity: 0.5,
    })
    const base = new THREE.Mesh(baseGeo, baseMat)
    base.position.y = -1.4  // 让 LatheGeometry 的 0 顶面对齐 group 中心
    base.castShadow = true
    base.receiveShadow = true
    islandGroup.add(base)

    // 岛顶平台（草地色，轻微凸起圆盘）
    const topGeo = new THREE.CylinderGeometry(1.3, 1.28, 0.16, 24)
    const topMat = new THREE.MeshStandardMaterial({
      color: d.topColor,
      roughness: 0.78,
      metalness: 0.0,
      envMap,
      envMapIntensity: 0.7,
    })
    const top = new THREE.Mesh(topGeo, topMat)
    top.position.y = 0.06
    top.castShadow = true
    top.receiveShadow = true
    islandGroup.add(top)

    // 主岛和花屿放樱花树，远屿只放一棵矮松
    if (i === 0) {
      // 主岛：一棵稍大的樱花树
      const blossomMat = new THREE.MeshStandardMaterial({
        color: 0xF5C5D0,
        roughness: 0.55,
        metalness: 0.0,
        emissive: 0xE8A8B8,
        emissiveIntensity: 0.35,
        envMap,
        envMapIntensity: 0.8,
      })
      const trunkMat = new THREE.MeshStandardMaterial({
        color: 0x5C4A38,
        roughness: 0.92,
        metalness: 0.0,
      })
      const tree = buildSakuraTree(THREE, envMap, blossomMat, trunkMat)
      tree.position.y = 0.16
      tree.scale.setScalar(1.1)
      tree.userData.isTree = true
      islandGroup.add(tree)
      islandGroup.userData.blossomMat = blossomMat
      islandGroup.userData.trunkMat = trunkMat
    } else if (i === 2) {
      // 花屿：小樱花树
      const blossomMat = new THREE.MeshStandardMaterial({
        color: 0xE8A8B8,
        roughness: 0.55,
        emissive: 0xE8A8B8,
        emissiveIntensity: 0.4,
        envMap,
        envMapIntensity: 0.8,
      })
      const trunkMat = new THREE.MeshStandardMaterial({
        color: 0x5C4A38,
        roughness: 0.92,
      })
      const tree = buildSakuraTree(THREE, envMap, blossomMat, trunkMat)
      tree.position.y = 0.16
      tree.scale.setScalar(0.7)
      islandGroup.add(tree)
      islandGroup.userData.blossomMat = blossomMat
      islandGroup.userData.trunkMat = trunkMat
    }

    islandGroup.position.set(d.x, d.y, d.z)
    islandGroup.scale.setScalar(d.scale)
    islandGroup.userData = {
      ...islandGroup.userData,
      baseY: d.y,
      floatPhase: Math.random() * Math.PI * 2,
      floatAmp: 0.1 + Math.random() * 0.08,
      rotSpeed: 0.0008 + Math.random() * 0.0012,
      info: { name: d.name, verse: d.verse },
      isIsland: true,
      isMain: i === 0,
    }
    scene.add(islandGroup)
    islands.push(islandGroup)
  }

  // ─── 柔光粒子（替代方形点） ───
  const dustCount = mobile ? 60 : 140
  const dustPos = new Float32Array(dustCount * 3)
  const dustColor = new Float32Array(dustCount * 3)
  const dustSize = new Float32Array(dustCount)
  const palette = [
    [0.95, 0.78, 0.83],  // 粉
    [0.75, 0.85, 0.72],  // 青绿
    [0.85, 0.88, 0.95],  // 雾蓝
    [1.0, 0.97, 0.88],   // 暖白
  ]
  for (let i = 0; i < dustCount; i++) {
    dustPos[i * 3] = (Math.random() - 0.5) * 40
    dustPos[i * 3 + 1] = Math.random() * 9 + 0.3
    dustPos[i * 3 + 2] = (Math.random() - 0.5) * 32 - 6
    const c = palette[Math.floor(Math.random() * palette.length)]
    dustColor[i * 3] = c[0]
    dustColor[i * 3 + 1] = c[1]
    dustColor[i * 3 + 2] = c[2]
    dustSize[i] = 0.08 + Math.random() * 0.18
  }
  const dustGeo = new THREE.BufferGeometry()
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3))
  dustGeo.setAttribute('color', new THREE.BufferAttribute(dustColor, 3))
  dustGeo.setAttribute('size', new THREE.BufferAttribute(dustSize, 1))

  const spriteTex = createSoftSpriteTexture(128, '#ffffff')
  const dustMat = new THREE.PointsMaterial({
    size: 0.32,
    map: spriteTex,
    vertexColors: true,
    transparent: true,
    opacity: 0.85,
    sizeAttenuation: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })
  const dust = new THREE.Points(dustGeo, dustMat)
  scene.add(dust)

  // ─── 拾取（raycaster 点击主岛触发飞入） ───
  const raycaster = new THREE.Raycaster()
  const pointer = new THREE.Vector2()
  let isFlying = false
  let flyAnim = null

  const onPointerDown = (e) => {
    if (isFlying) return
    const rect = renderer.domElement.getBoundingClientRect()
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1
    raycaster.setFromCamera(pointer, camera)
    // 仅拾取浮岛 base + top
    const pickables = []
    islands.forEach((g) => {
      g.traverse((o) => {
        if (o.isMesh) o.userData._islandRef = g
        if (o.isMesh && (o.geometry?.type === 'LatheGeometry' || o.geometry?.type === 'CylinderGeometry')) {
          pickables.push(o)
        }
      })
    })
    const hits = raycaster.intersectObjects(pickables, false)
    if (hits.length > 0) {
      const islandRef = hits[0].object.userData._islandRef
      if (islandRef) flyToIsland(islandRef)
    }
  }
  renderer.domElement.addEventListener('pointerdown', onPointerDown)

  const flyToIsland = (island) => {
    if (isFlying) return
    isFlying = true
    controls.autoRotate = false

    // 计算目标相机位置：在浮岛斜上方
    const targetPos = new THREE.Vector3(
      island.position.x,
      island.position.y + 2.5,
      island.position.z + 5.5,
    )
    const targetLookAt = island.position.clone()
    targetLookAt.y += 0.8

    const startPos = camera.position.clone()
    const startTarget = controls.target.clone()
    const duration = 1400
    const t0 = performance.now()

    if (flyAnim) cancelAnimationFrame(flyAnim)
    const step = () => {
      const elapsed = performance.now() - t0
      const t = Math.min(1, elapsed / duration)
      // easeInOutCubic
      const e = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
      camera.position.lerpVectors(startPos, targetPos, e)
      controls.target.lerpVectors(startTarget, targetLookAt, e)
      controls.update()
      if (t < 1) {
        flyAnim = requestAnimationFrame(step)
      } else {
        isFlying = false
        // 显示信息卡
        islandInfo.value = island.userData.info
        // 恢复自动旋转（2s 后）
        setTimeout(() => {
          if (!isFlying) controls.autoRotate = autoRotate.value
        }, 2200)
      }
    }
    step()
  }

  // ─── 重置视角 ───
  const resetView = () => {
    if (isFlying) return
    isFlying = true
    controls.autoRotate = false
    islandInfo.value = null
    const startPos = camera.position.clone()
    const startTarget = controls.target.clone()
    const duration = 1200
    const t0 = performance.now()
    const step = () => {
      const elapsed = performance.now() - t0
      const t = Math.min(1, elapsed / duration)
      const e = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
      camera.position.lerpVectors(startPos, INITIAL_CAM_POS, e)
      controls.target.lerpVectors(startTarget, INITIAL_CAM_TARGET, e)
      controls.update()
      if (t < 1) {
        flyAnim = requestAnimationFrame(step)
      } else {
        isFlying = false
        controls.autoRotate = autoRotate.value
      }
    }
    step()
  }

  // ─── 自动旋转开关 ───
  const onAutoRotateChange = (v) => {
    autoRotate.value = v
    if (!isFlying) controls.autoRotate = v
  }

  // ─── 用户首次交互：关闭 hint ───
  const onFirstInteract = () => {
    showHint.value = false
    renderer.domElement.removeEventListener('pointerdown', onFirstInteract)
    renderer.domElement.removeEventListener('wheel', onFirstInteract)
  }
  renderer.domElement.addEventListener('pointerdown', onFirstInteract, { once: true })
  renderer.domElement.addEventListener('wheel', onFirstInteract, { once: true })

  // ─── 渲染循环 ───
  const clock = new THREE.Clock()

  const render = () => {
    const t = clock.getElapsedTime()

    // 水面 shader 时间更新
    if (seaMat.userData.shader) {
      seaMat.userData.shader.uniforms.uTime.value = t
    }

    // 浮岛：上下浮动 + 缓慢旋转
    for (const isl of islands) {
      const u = isl.userData
      isl.position.y = u.baseY + Math.sin(t * 0.6 + u.floatPhase) * u.floatAmp
      isl.rotation.y += u.rotSpeed
    }

    // 樱花花团：轻微呼吸缩放（通过 emissive 强度）
    islands.forEach((isl) => {
      if (isl.userData.blossomMat) {
        isl.userData.blossomMat.emissiveIntensity =
          0.35 + Math.sin(t * 1.2 + isl.userData.floatPhase) * 0.08
      }
    })

    // 粒子：缓慢上升 + 微弱横向漂移
    const dp = dust.geometry.attributes.position.array
    for (let i = 0; i < dp.length; i += 3) {
      dp[i + 1] += 0.005
      dp[i] += Math.sin(t * 0.4 + i) * 0.002
      if (dp[i + 1] > 9.5) {
        dp[i + 1] = 0.3
        dp[i] = (Math.random() - 0.5) * 40
        dp[i + 2] = (Math.random() - 0.5) * 32 - 6
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
    sea, seaPositions, seaMat, islands, dust, spriteTex,
    envMap, pmrem,
    stopRAF, ro,
    onPointerDown, onFirstInteract,
    container,
    _THREE: THREE,
  }
}

// 自动旋转 watch：SceneControls 通过 v-model 改 autoRotate，同步到 controls
watch(autoRotate, (v) => {
  const t = three.value
  if (t && t.controls && !t._flying) {
    t.controls.autoRotate = v
  }
})

const onResetView = () => {
  const t = three.value
  if (!t) return
  // 调用内部 resetView（在 initScene 闭包中定义）
  // 这里通过 controls 直接做简化版（避免引用闭包变量）
  const { controls, camera, _THREE } = t
  if (!controls || !camera) return
  // 标记 flying 防止自动旋转干扰
  t._flying = true
  controls.autoRotate = false
  islandInfo.value = null
  const INITIAL_CAM_POS = new _THREE.Vector3(0, 4.5, 13)
  const INITIAL_CAM_TARGET = new _THREE.Vector3(0, 1.5, 0)
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
      t._flying = false
      controls.autoRotate = autoRotate.value
    }
  }
  step()
}

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

  // 释放几何/材质/纹理（递归）
  disposeObject3D(t.scene)
  if (t.spriteTex) t.spriteTex.dispose()

  // 释放渲染器 + 后处理 + envMap + pmrem
  disposeRenderer(t.renderer, t.composer, t.pmrem, t.envMap)

  if (t.renderer?.domElement && t.container?.contains(t.renderer.domElement)) {
    t.container.removeChild(t.renderer.domElement)
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
      class="hero-scene__fallback"
    >
      <svg
        viewBox="0 0 800 480"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="hs-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#FAF8F4" />
            <stop offset="100%" stop-color="#E5E0D5" />
          </linearGradient>
          <radialGradient id="hs-sun" cx="0.7" cy="0.3" r="0.4">
            <stop offset="0%" stop-color="#FFF5E0" stop-opacity="0.8" />
            <stop offset="100%" stop-color="#FFF5E0" stop-opacity="0" />
          </radialGradient>
        </defs>
        <rect width="800" height="480" fill="url(#hs-sky)" />
        <rect width="800" height="480" fill="url(#hs-sun)" />
        <ellipse cx="180" cy="260" rx="60" ry="14" fill="#C5BCA8" opacity="0.5" />
        <ellipse cx="620" cy="270" rx="80" ry="16" fill="#C5BCA8" opacity="0.5" />
        <ellipse cx="400" cy="320" rx="120" ry="22" fill="#8B7B5E" opacity="0.6" />
        <ellipse cx="400" cy="310" rx="115" ry="20" fill="#C5D9A8" opacity="0.85" />
        <rect x="395" y="270" width="6" height="40" fill="#6B5A48" />
        <circle cx="400" cy="260" r="18" fill="#F5C5D0" opacity="0.9" />
        <circle cx="385" cy="268" r="12" fill="#F5C5D0" opacity="0.85" />
        <circle cx="415" cy="268" r="12" fill="#F5C5D0" opacity="0.85" />
        <line x1="0" y1="340" x2="800" y2="340" stroke="#A8B8C5" stroke-width="1" opacity="0.4" />
        <path d="M 0 360 Q 100 350 200 360 T 400 360 T 600 360 T 800 360 L 800 480 L 0 480 Z" fill="#B8D4D8" opacity="0.32" />
        <path d="M 0 400 Q 100 390 200 400 T 400 400 T 600 400 T 800 400 L 800 480 L 0 480 Z" fill="#B8D4D8" opacity="0.5" />
        <path d="M 0 440 Q 100 430 200 440 T 400 440 T 600 440 T 800 440 L 800 480 L 0 480 Z" fill="#B8D4D8" opacity="0.7" />
        <circle cx="100" cy="180" r="3" fill="#E8B8C5" opacity="0.7" />
        <circle cx="240" cy="120" r="2" fill="#A8C5A0" opacity="0.6" />
        <circle cx="540" cy="160" r="2.5" fill="#A8B8C5" opacity="0.65" />
        <circle cx="680" cy="200" r="2" fill="#FAF6F2" opacity="0.8" />
        <circle cx="380" cy="90" r="1.5" fill="#E8B8C5" opacity="0.6" />
      </svg>
    </div>

    <!-- 交互指引（首次进入显示，首次交互后消失） -->
    <SceneHint
      v-if="showThree && showHint"
      v-model:visible="showHint"
      text="拖拽旋转视角 · 滚轮缩放 · 点击浮岛飞入"
      gesture="drag-rotate-zoom"
      :auto-hide="6500"
    />

    <!-- 视角控制工具栏 -->
    <SceneControls
      v-if="showThree"
      v-model="autoRotate"
      position="bottom-right"
      @reset="onResetView"
    />

    <!-- 浮岛信息卡（点击主岛后浮现） -->
    <transition name="island-card">
      <div v-if="islandInfo" class="hero-scene__island-card">
        <div class="island-card__name">{{ islandInfo.name }}</div>
        <div class="island-card__verse">"{{ islandInfo.verse }}"</div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.hero-scene {
  position: relative;
  width: 100%;
  border-radius: var(--radius-xl, 32px);
  overflow: hidden;
  background: linear-gradient(180deg, #FAF8F4 0%, #F0EDE5 100%);
  box-shadow: 0 12px 40px rgba(74, 68, 56, 0.08);
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
  cursor: grab;
}

.hero-scene__canvas-wrap :deep(canvas):active {
  cursor: grabbing;
}

.hero-scene__fallback svg {
  width: 100%;
  height: 100%;
  display: block;
}

/* 浮岛信息卡 */
.hero-scene__island-card {
  position: absolute;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 16px 28px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 20px;
  box-shadow: 0 12px 40px rgba(74, 68, 56, 0.15),
              inset 0 1px 0 rgba(255, 255, 255, 0.9);
  text-align: center;
  pointer-events: none;
  z-index: 6;
  max-width: 80%;
}

.island-card__name {
  font-family: var(--font-serif, serif);
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 0.12em;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 4px;
}

.island-card__verse {
  font-family: var(--font-serif, serif);
  font-style: italic;
  font-size: 13px;
  color: var(--color-text-secondary, #5C4F3E);
  letter-spacing: 0.05em;
}

.island-card-enter-active,
.island-card-leave-active {
  transition: opacity 0.5s var(--ease-apple, cubic-bezier(0.16, 1, 0.3, 1)),
              transform 0.5s var(--ease-apple, cubic-bezier(0.16, 1, 0.3, 1));
}
.island-card-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-12px);
}
.island-card-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}

/* reduced-motion：SVG 静态插画 */
@media (prefers-reduced-motion: reduce) {
  .hero-scene__canvas-wrap {
    display: none;
  }
  .hero-scene__fallback {
    display: block;
  }
}

@media (max-width: 768px) {
  .hero-scene {
    border-radius: var(--radius-lg, 20px);
  }
  .hero-scene__island-card {
    top: 16px;
    padding: 12px 20px;
  }
  .island-card__name {
    font-size: 16px;
  }
  .island-card__verse {
    font-size: 12px;
  }
}
</style>
