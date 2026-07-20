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
let _reducedMotion = null
let _isMobile = null
let _isLowPower = null

/**
 * 检测浏览器是否支持 WebGL（用于 Three.js 重度场景的准入判断）
 * 仅检测 WebGL2，因为 Three.js 0.168 默认走 WebGL2
 */
export function hasWebGL() {
  if (_webglChecked) return _webglAvailable
  _webglChecked = true
  try {
    const canvas = document.createElement('canvas')
    const gl =
      canvas.getContext('webgl2') ||
      canvas.getContext('webgl') ||
      canvas.getContext('experimental-webgl')
    _webglAvailable = !!(gl && gl instanceof WebGLRenderingContext) ||
      !!(canvas.getContext('webgl2') instanceof WebGL2RenderingContext)
  } catch (e) {
    _webglAvailable = false
  }
  return _webglAvailable
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
 * 综合：核心数、设备内存、节电模式
 */
export function isLowPower() {
  if (_isLowPower !== null) return _isLowPower
  if (typeof navigator === 'undefined') {
    _isLowPower = false
    return false
  }
  const cores = navigator.hardwareConcurrency || 4
  const memory = navigator.deviceMemory || 4
  // 节电模式（实验性 API，仅部分浏览器支持）
  const saveData =
    navigator.connection && navigator.connection.saveData === true
  _isLowPower = cores <= 4 || memory <= 2 || saveData
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
