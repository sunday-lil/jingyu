/**
 * 视觉增强工具：能力检测 + 性能预算
 *
 * 设计原则：
 * - 渐进增强：低性能/老浏览器/无障碍场景自动降级，不报错
 * - 性能可控：移动端、节电模式、reduced-motion 一律关重度效果
 * - 单次检测、缓存结果（同次会话不重复 probe）
 */

let _webglChecked = false
let _webglAvailable = false
let _webglCaps = null
let _reducedMotion = null
let _isMobile = null
let _isLowPower = null

/**
 * 检测浏览器是否支持 WebGL（用于 Three.js 重度场景的准入判断）
 * 同时检测关键扩展能力（half-float / max texture size），缓存到 _webglCaps
 *
 * Safari 兼容性（v2.3.3 修复）：
 * - 明确区分 WebGL1/WebGL2（旧逻辑用 instanceof WebGLRenderingContext 误判 WebGL2 context）
 * - 检测 EXT_color_buffer_half_float（PMREM/Bloom 必需，老 iOS 缺失）
 * - 检测 MAX_TEXTURE_SIZE / MAX_CUBE_MAP_TEXTURE_SIZE（shadow map 2048 / PMREM 依赖）
 */
export function hasWebGL() {
  if (_webglChecked) return _webglAvailable
  _webglChecked = true
  try {
    const canvas = document.createElement('canvas')
    let gl = canvas.getContext('webgl2', { failIfMajorPerformanceCaveat: false })
    const isWebGL2 = !!gl
    if (!gl) {
      gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    }
    if (!gl) {
      _webglAvailable = false
      return false
    }

    const exts = gl.getSupportedExtensions() || []
    const hasHalfFloat = exts.includes('EXT_color_buffer_half_float') ||
                         exts.includes('EXT_color_buffer_float')
    const hasHalfFloatLinear = exts.includes('OES_texture_half_float_linear')
    const maxTexSize = gl.getParameter(gl.MAX_TEXTURE_SIZE)
    const maxCubeSize = gl.getParameter(gl.MAX_CUBE_MAP_TEXTURE_SIZE)

    _webglCaps = {
      isWebGL2,
      hasHalfFloat,
      hasHalfFloatLinear,
      maxTexSize,
      maxCubeSize,
      // PMREM 需要 half-float + cube map ≥1024
      canPMREM: hasHalfFloat && maxCubeSize >= 1024,
      // UnrealBloomPass 需要 half-float + half-float linear
      canBloom: hasHalfFloat && hasHalfFloatLinear,
    }

    // WebGL 可用门槛：有 WebGL2 或 WebGL1 + 纹理尺寸够
    _webglAvailable = isWebGL2 || maxTexSize >= 4096
  } catch (e) {
    _webglAvailable = false
  }
  return _webglAvailable
}

/**
 * 获取 WebGL 能力详情（hasWebGL() 后才有效）
 * 用于 HeroScene 决定是否降级 PMREM/Bloom
 */
export function getWebGLCaps() {
  return _webglCaps
}

/**
 * 是否为 Safari（v2.3.3 加，用于 3D 场景降级决策）
 * Safari 的 WebKit 引擎对 WebGL 有已知 bug（iOS 17 上下文丢失、PMREM 静默失败等）
 */
export function isSafari() {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent || ''
  // Safari = WebKit + 非 Chrome/Android
  return /Safari/i.test(ua) && !/Chrome|CriOS|Android/i.test(ua)
}

/**
 * 是否为 iOS（v2.3.3 加，用于 3D 场景降级决策）
 * iPhone/iPad/iPod，iPadOS 13+ 的 iPad 报 MacIntel 但有触摸
 */
export function isIOS() {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent || ''
  return /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
}

/**
 * 用户是否启用了「减少动态效果」无障碍偏好
 * 监听变化，长期有效
 */
export function prefersReducedMotion() {
  if (_reducedMotion !== null) return _reducedMotion
  if (typeof window === 'undefined' || !window.matchMedia) {
    _reducedMotion = false
    return false
  }
  const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
  _reducedMotion = mq.matches
  // 监听变化（用户切到 reduced-motion 时立即生效）
  try {
    mq.addEventListener('change', (e) => {
      _reducedMotion = e.matches
    })
  } catch (_) {
    // Safari < 14 fallback
    mq.addListener((e) => {
      _reducedMotion = e.matches
    })
  }
  return _reducedMotion
}

/**
 * 是否为移动端（touch 优先 + 窄屏）
 * 用于：减少粒子数 / 关闭重度 Three.js 场景
 */
export function isMobile() {
  if (_isMobile !== null) return _isMobile
  if (typeof window === 'undefined') {
    _isMobile = false
    return false
  }
  const ua = navigator.userAgent || ''
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0
  const narrow = window.matchMedia('(max-width: 768px)').matches
  _isMobile = hasTouch && (narrow || /Mobi|Android|iPhone|iPad/i.test(ua))
  return _isMobile
}

/**
 * 是否为低性能设备（启发式）
 *
 * Safari 兼容性（v2.3.4 修复）：
 * - iOS Safari 的 navigator.hardwareConcurrency 经常返回 undefined 或较小值（如 4）
 * - 旧逻辑 `cores <= 4` 把所有 iPhone 误判为低性能 → shouldUseThreeJS() 返回 false
 *   → FlowerField 不渲染 3D（用户看到纯色渐变而非 3D 花田）
 * - 新逻辑：只有明确的低性能信号才降级（节电 / 内存≤2GB / 核心数≤2）
 */
export function isLowPower() {
  if (_isLowPower !== null) return _isLowPower
  if (typeof navigator === 'undefined') {
    _isLowPower = false
    return false
  }
  // 注意：不 fallback 到 4，undefined 表示「未知」而非「低性能」
  const cores = navigator.hardwareConcurrency
  const memory = navigator.deviceMemory
  // 节电模式（实验性 API，仅部分浏览器支持）
  const saveData =
    navigator.connection && navigator.connection.saveData === true
  // 只有明确信号才判为低性能：
  // - 节电模式开启
  // - 内存 ≤ 2GB（老设备）
  // - 核心数明确 ≤ 2（非常老旧的设备，undefined 不算）
  _isLowPower = saveData || memory <= 2 || (cores !== undefined && cores <= 2)
  return _isLowPower
}

/**
 * 综合判断：是否允许启用 Three.js 重度场景
 * - 不支持 WebGL → false
 * - reduced-motion → false
 * - 低性能设备 → false（移动端用 CSS 降级）
 */
export function shouldUseThreeJS() {
  return hasWebGL() && !prefersReducedMotion() && !isLowPower()
}

/**
 * 综合判断：是否允许启用 Canvas2D 中度场景
 * - reduced-motion → false（CSS 静态背景兜底）
 * - 移动端允许，但调用方应自行减少粒子数
 */
export function shouldUseCanvas() {
  return !prefersReducedMotion()
}

/**
 * 适配 rAF 节流：在不可见标签页自动暂停
 * 返回一个安全的 rAF（隐藏时跳过）
 */
export function smartRAF(callback) {
  let rafId = null
  const loop = (ts) => {
    if (document.hidden) {
      // 标签页隐藏，暂停；可见时自动恢复
      rafId = null
      const onVisible = () => {
        if (!document.hidden) {
          document.removeEventListener('visibilitychange', onVisible)
          rafId = requestAnimationFrame(loop)
        }
      }
      document.addEventListener('visibilitychange', onVisible)
      return
    }
    callback(ts)
    rafId = requestAnimationFrame(loop)
  }
  rafId = requestAnimationFrame(loop)
  return () => {
    if (rafId) cancelAnimationFrame(rafId)
    rafId = null
  }
}
