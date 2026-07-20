/**
 * Three.js 现代化渲染管线工具集
 *
 * 解决问题：
 * - 旧实现用 MeshLambertMaterial + PointsMaterial 平面点，视觉粗糙像红白机
 * - 没有环境光、阴影、Bloom、色调映射，缺乏现代感
 * - 没有统一 OrbitControls 交互，用户不知道怎么操作 3D
 *
 * 本模块提供：
 * - createRenderer: PBR 渲染器（ACES Filmic + sRGB + PCFSoftShadowMap）
 * - createEnvironment: RoomEnvironment 环境贴图（让 PBR 材质有真实反射）
 * - createPostProcessing: EffectComposer + UnrealBloomPass + OutputPass
 * - createOrbitControls: 统一交互约束的 OrbitControls
 * - disposeObject3D / disposeRenderer: 严格释放，避免内存泄漏
 *
 * 设计原则：
 * - 所有 addon 走 `three/addons/` 子路径，便于 tree-shaking
 * - 函数式工厂，组件按需取用，不强依赖
 * - 移动端/低性能由调用方结合 visual.js 判断后再传入参数
 *
 * 关联文档：HANDOFF §5.10 视觉策略 / §6.23 视觉组件 4 铁律
 */

import * as THREE from 'three'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js'

/**
 * 创建现代 PBR 渲染器
 *
 * @param {HTMLCanvasElement} canvas
 * @param {Object} [opts]
 * @param {number} [opts.dpr=1] - 设备像素比上限（移动端建议 ≤1.5）
 * @param {boolean} [opts.shadows=true] - 是否启用软阴影
 * @param {number} [opts.toneMappingExposure=1.0] - ACES 曝光
 * @returns {THREE.WebGLRenderer}
 */
export function createRenderer(canvas, opts = {}) {
  const {
    dpr = 1,
    shadows = true,
    toneMappingExposure = 1.0,
  } = opts

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance',
    stencil: false,
    depth: true,
  })

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, dpr))
  // ACES Filmic 是电影工业标准的色调映射，能优雅处理高光过曝
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = toneMappingExposure
  // sRGB 输出空间，让颜色与设计稿一致
  renderer.outputColorSpace = THREE.SRGBColorSpace

  if (shadows) {
    renderer.shadowMap.enabled = true
    // PCFSoftShadowMap 边缘更柔和，比 BasicPCF 更现代
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
  }

  return renderer
}

/**
 * 创建 PBR 环境贴图（RoomEnvironment 程序化生成，无外部 HDR 文件依赖）
 *
 * 调用方需要保存返回的 envMap，在 onBeforeUnmount 中调用 envMap.dispose()
 *
 * @param {THREE.WebGLRenderer} renderer
 * @param {number} [size=256] - 环境贴图分辨率（移动端可降到 128）
 * @returns {{ envMap: THREE.Texture, pmrem: THREE.PMREMGenerator }}
 */
export function createEnvironment(renderer, size = 256) {
  const pmrem = new THREE.PMREMGenerator(renderer)
  const envScene = new RoomEnvironment()
  const envMap = pmrem.fromScene(envScene, 0.04).texture
  envScene.dispose && envScene.dispose()
  return { envMap, pmrem }
}

/**
 * 创建后处理管线：RenderPass → UnrealBloomPass → OutputPass
 *
 * @param {THREE.Scene} scene
 * @param {THREE.Camera} camera
 * @param {THREE.WebGLRenderer} renderer
 * @param {Object} [opts]
 * @param {boolean} [opts.bloom=true] - 是否启用 Bloom
 * @param {number} [opts.strength=0.6] - Bloom 强度（柔和光晕，避免过曝）
 * @param {number} [opts.radius=0.4] - Bloom 半径
 * @param {number} [opts.threshold=0.85] - 仅高亮区域参与 Bloom
 * @returns {EffectComposer}
 */
export function createPostProcessing(scene, camera, renderer, opts = {}) {
  const {
    bloom = true,
    strength = 0.6,
    radius = 0.4,
    threshold = 0.85,
  } = opts

  const composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))

  if (bloom) {
    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      strength,
      radius,
      threshold,
    )
    composer.addPass(bloomPass)
  }

  // OutputPass 负责正确的色调映射 + 颜色空间转换（必须在最后）
  composer.addPass(new OutputPass())

  return composer
}

/**
 * 创建统一约束的 OrbitControls
 *
 * 默认策略：
 * - 限制极角（不能转到地下/天上）
 * - 禁用平移（避免用户拖出场景）
 * - 阻尼开启（拖动有惯性感，符合现代交互）
 * - 移动端单指旋转、双指缩放
 *
 * @param {THREE.Camera} camera
 * @param {HTMLElement} domElement
 * @param {Object} [opts]
 * @param {boolean} [opts.enablePan=false]
 * @param {boolean} [opts.enableZoom=true]
 * @param {boolean} [opts.enableRotate=true]
 * @param {boolean} [opts.autoRotate=false] - 闲置时自动旋转
 * @param {number} [opts.autoRotateSpeed=0.4]
 * @param {number} [opts.minDistance=4]
 * @param {number} [opts.maxDistance=20]
 * @param {number} [opts.minPolarAngle=0.1]
 * @param {number} [opts.maxPolarAngle=Math.PI / 2 - 0.05] - 不让镜头穿越地面
 * @param {number} [opts.dampingFactor=0.06]
 * @param {number} [opts.rotateSpeed=0.7]
 * @returns {OrbitControls}
 */
export function createOrbitControls(camera, domElement, opts = {}) {
  const controls = new OrbitControls(camera, domElement)

  controls.enableDamping = true
  controls.dampingFactor = opts.dampingFactor ?? 0.06
  controls.rotateSpeed = opts.rotateSpeed ?? 0.7
  controls.enablePan = opts.enablePan ?? false
  controls.enableZoom = opts.enableZoom ?? true
  controls.enableRotate = opts.enableRotate ?? true

  controls.autoRotate = opts.autoRotate ?? false
  controls.autoRotateSpeed = opts.autoRotateSpeed ?? 0.4

  controls.minDistance = opts.minDistance ?? 4
  controls.maxDistance = opts.maxDistance ?? 20
  controls.minPolarAngle = opts.minPolarAngle ?? 0.1
  controls.maxPolarAngle = opts.maxPolarAngle ?? Math.PI / 2 - 0.05

  return controls
}

/**
 * 递归释放 Object3D 及其子节点的 geometry / material
 *
 * 注意：
 * - 不会释放纹理（material.map 等），需要单独调用 disposeTexture
 * - 调用前应将对象从 scene 中 remove
 *
 * @param {THREE.Object3D} obj
 */
export function disposeObject3D(obj) {
  if (!obj) return
  obj.traverse((node) => {
    if (node.isMesh || node.isLine || node.isPoints) {
      if (node.geometry) {
        node.geometry.dispose()
      }
      const mats = Array.isArray(node.material) ? node.material : [node.material]
      mats.forEach((m) => {
        if (!m) return
        // 释放材质上挂载的纹理
        Object.keys(m).forEach((key) => {
          const v = m[key]
          if (v && v.isTexture) v.dispose()
        })
        m.dispose()
      })
    }
  })
}

/**
 * 完整释放渲染器 + 后处理管线
 *
 * @param {THREE.WebGLRenderer} renderer
 * @param {EffectComposer} [composer]
 * @param {THREE.PMREMGenerator} [pmrem]
 * @param {THREE.Texture} [envMap]
 */
export function disposeRenderer(renderer, composer, pmrem, envMap) {
  if (composer) {
    composer.passes.forEach((p) => {
      if (p.dispose) p.dispose()
    })
    composer.renderTarget1 && composer.renderTarget1.dispose()
    composer.renderTarget2 && composer.renderTarget2.dispose()
  }
  if (envMap) envMap.dispose()
  if (pmrem) pmrem.dispose()
  if (renderer) {
    renderer.dispose()
    renderer.forceContextLoss && renderer.forceContextLoss()
  }
}

/**
 * 创建一个柔光圆点 sprite 纹理（程序化生成，无外部图片依赖）
 *
 * 用于替代粗糙的方形 PointsMaterial，让粒子有现代柔和质感
 *
 * @param {number} [size=128]
 * @param {string} [color='#ffffff']
 * @returns {THREE.CanvasTexture}
 */
export function createSoftSpriteTexture(size = 128, color = '#ffffff') {
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = size
  const ctx = canvas.getContext('2d')
  const cx = size / 2
  const cy = size / 2
  const r = size / 2
  const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, r)
  gradient.addColorStop(0, color)
  gradient.addColorStop(0.3, color)
  gradient.addColorStop(0.7, 'rgba(255,255,255,0.3)')
  gradient.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, size, size)

  const tex = new THREE.CanvasTexture(canvas)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

/**
 * 创建主光源（带阴影）
 *
 * @param {Object} [opts]
 * @param {number[]} [opts.position=[8, 14, 6]]
 * @param {number} [opts.intensity=2.2]
 * @param {number} [opts.color=0xfff4e0]
 * @param {Object} [opts.shadow]
 * @param {number} [opts.shadow.mapSize=2048]
 * @param {number} [opts.shadow.camera.near=0.5]
 * @param {number} [opts.shadow.camera.far=60]
 * @param {number} [opts.shadow.camera.left=-20]
 * @param {number} [opts.shadow.camera.right=20]
 * @param {number} [opts.shadow.camera.top=20]
 * @param {number} [opts.shadow.camera.bottom=-20]
 * @param {number} [opts.shadow.bias=-0.0005]
 * @returns {THREE.DirectionalLight}
 */
export function createKeyLight(opts = {}) {
  const {
    position = [8, 14, 6],
    intensity = 2.2,
    color = 0xfff4e0,
    shadow = {},
  } = opts

  const light = new THREE.DirectionalLight(color, intensity)
  light.position.set(...position)
  light.castShadow = true
  light.shadow.mapSize.set(shadow.mapSize ?? 2048, shadow.mapSize ?? 2048)
  light.shadow.camera.near = shadow.camera?.near ?? 0.5
  light.shadow.camera.far = shadow.camera?.far ?? 60
  light.shadow.camera.left = shadow.camera?.left ?? -20
  light.shadow.camera.right = shadow.camera?.right ?? 20
  light.shadow.camera.top = shadow.camera?.top ?? 20
  light.shadow.camera.bottom = shadow.camera?.bottom ?? -20
  light.shadow.bias = shadow.bias ?? -0.0005
  light.shadow.radius = shadow.radius ?? 4
  return light
}

/**
 * 创建补光（无阴影，半球光，给阴影区填色）
 *
 * @param {number[]} [opts.color=0xfff0e0] 天空色
 * @param {number[]} [opts.groundColor=0x6b5a48] 地面色
 * @param {number} [opts.intensity=0.4]
 * @returns {THREE.HemisphereLight}
 */
export function createFillLight(opts = {}) {
  const {
    color = 0xfff0e0,
    groundColor = 0x6b5a48,
    intensity = 0.4,
  } = opts
  return new THREE.HemisphereLight(color, groundColor, intensity)
}
