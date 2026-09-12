<script setup>
import { onMounted, ref, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { gsap } from 'gsap'
import { prefersReducedMotion } from '@/utils/visual'
import { GUIDE_SECTIONS } from '@/data/islandGuide'

// 异步加载 Three.js 浮岛雾海场景（按需加载，减小首屏包）
const HeroScene = defineAsyncComponent(() =>
  import('@/components/HeroScene.vue')
)

const router = useRouter()
const userStore = useUserStore()

// 岛上指南手风琴展开状态（v2.5.0：复用共享指南数据，与个人主页一致）
const guideOpen = ref(null)

// 六个功能板块入口（v2.3：四字文艺命名 + 岛屿图标）
// v2.4.2：花坊 → 落叶花坊；漂流日记 🍶 → 🏺
// 名字已确认：琴音疗心 / 漂流日记 / 情绪日历 / 心语树洞 / 落叶花坊 / 屿上花田
// v2.5.0：reward「怎么玩」一行 —— 与 islandGuide.js 的 reward 字段保持同步
const modules = [
  {
    label: '琴音疗心',
    desc: '宫商角徵羽 · 古琴五音调情志',
    reward: '每听一曲 +1 露水 · 听满 10 首解锁「琴音知音」徽章',
    icon: '🎵',
    to: '/music',
    color: 'linear-gradient(135deg, #E8D5A8 0%, #D4C18A 100%)',
  },
  {
    label: '漂流日记',
    desc: '把心事写进瓶子 · 让它漂向远方',
    reward: '每写一篇 +2 露水 · 拾瓶与留鼓励亦有露水',
    icon: '🏺',
    to: '/diary',
    color: 'linear-gradient(135deg, #A8C5E8 0%, #C5D5E8 100%)',
  },
  {
    label: '情绪日历',
    desc: '记录每天的心情轨迹',
    reward: '每次打卡 +1 露水 · 连续 7 天解锁「七日静心」徽章',
    icon: '🌙',
    to: '/calendar',
    color: 'linear-gradient(135deg, #C5C5E8 0%, #E8D5E8 100%)',
  },
  {
    label: '心语树洞',
    desc: '说给一棵树听 · 它不会告诉任何人',
    reward: '倾诉心事 · 对话满 20 次解锁「树洞倾心」徽章',
    icon: '🌳',
    to: '/ai-chat',
    color: 'linear-gradient(135deg, #B8C5E8 0%, #A8D5BA 100%)',
  },
  {
    label: '落叶花坊',
    desc: '落叶归根 · 化作春泥换花种',
    reward: '落叶换花种 · 露水换装扮与小动物',
    icon: '🍂',
    to: '/shop',
    color: 'linear-gradient(135deg, #E8C5A8 0%, #D5A875 100%)',
  },
  {
    label: '屿上花田',
    desc: '在静屿种下你的花朵',
    reward: '露水浇灌至花开 · 枯花拾取化作落叶',
    icon: '🌸',
    to: '/garden',
    color: 'linear-gradient(135deg, #E8B8C5 0%, #F5D5C5 100%)',
  },
]

// ─── 模块卡片 3D 鼠标倾斜 ───
const TILT_MAX = 6
const onModuleCardMove = (e) => {
  if (prefersReducedMotion()) return
  const card = e.currentTarget
  const rect = card.getBoundingClientRect()
  const x = (e.clientX - rect.left) / rect.width - 0.5
  const y = (e.clientY - rect.top) / rect.height - 0.5
  card.style.transform = `perspective(800px) rotateY(${x * TILT_MAX}deg) rotateX(${-y * TILT_MAX}deg) translateY(-4px)`
}
const onModuleCardLeave = (e) => {
  const card = e.currentTarget
  card.style.transform = ''
}

// 点击滚动提示 → 平滑滚到「岛上各处」板块
const scrollToModules = () => {
  document.querySelector('.module-section')?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

onMounted(() => {
  // Hero 入场动效（只做位移，不设 opacity/scale 初始态，防动画中断后永久不可见）
  const tl = gsap.timeline({ delay: 0.2 })
  tl.from('.hero-verse', { y: 20, duration: 1, ease: 'power3.out' })
    .from('.hero-title', { y: 30, duration: 1.2, ease: 'power4.out' }, '-=0.6')
    .from('.hero__intro', { y: 26, duration: 1, ease: 'power3.out' }, '-=0.9')
    .from('.module-card', {
      y: 30, duration: 0.7, stagger: 0.08, ease: 'power3.out'
    }, '-=0.4')
    .from('.guide-card', {
      y: 24, duration: 0.6, stagger: 0.06, ease: 'power3.out'
    }, '-=0.4')

  // 岛屿图标持续呼吸
  gsap.to('.hero-icon', {
    scale: 1.06, duration: 4, repeat: -1, yoyo: true, ease: 'sine.inOut'
  })
})
</script>

<template>
  <div class="home">
    <!-- Hero 区：3D 浮岛雾海 + 静屿名称与理念（v2.5.0：左品牌 / 右理念卡） -->
    <section class="hero">
      <HeroScene class="hero__scene" height="520px" />
      <div class="hero__content">
        <!-- v2.4.2：海浪图标（替代原沙滩🏝️，更贴合"静屿"海意） -->
        <div class="hero__brand">
          <div class="hero-icon">🌊</div>
          <p class="hero-verse">"潮声不止，心安自屿。"</p>
          <h1 class="hero-title">静屿</h1>
        </div>
        <!-- v2.5.0：心灵港湾理念卡（私密 · 疗愈 · 生长三句 + 信任点） -->
        <div class="hero__intro">
          <p class="hero__intro-lead">每一个情绪，都值得一座岛。</p>
          <p class="hero__intro-body">
            静屿是一座只属于你的心灵港湾——<br>
            听一曲古琴，写一封漂流的信，<br>
            把说不出口的，种成一朵会开的花。
          </p>
          <p class="hero__intro-trust">🔒 日记端到端加密 · 无广告 · 无算法推荐</p>
        </div>
      </div>
      <button
        type="button"
        class="hero__scroll-hint"
        aria-label="向下滚动到岛上各处"
        @click="scrollToModules"
      >
        <span>向下，遇见岛上的去处</span>
        <span class="hero__scroll-arrow">↓</span>
      </button>
    </section>

    <!-- v2.3：六个功能板块入口（四字文艺命名；v2.5.0：卡内加「怎么玩」奖励行） -->
    <section class="module-section">
      <h2 class="section-title">岛上各处</h2>
      <p class="section-subtitle">六个去处 · 任选一处歇脚</p>
      <div class="module-grid">
        <router-link
          v-for="m in modules"
          :key="m.label"
          :to="m.to"
          class="module-card"
          @mousemove="onModuleCardMove"
          @mouseleave="onModuleCardLeave"
        >
          <div class="module-card__icon" :style="{ background: m.color }">{{ m.icon }}</div>
          <div class="module-card__body">
            <div class="module-card__title">{{ m.label }}</div>
            <div class="module-card__desc">{{ m.desc }}</div>
            <div class="module-card__reward">✦ {{ m.reward }}</div>
          </div>
          <div class="module-card__arrow">→</div>
        </router-link>
      </div>
    </section>

    <!-- v2.5.0：岛上指南（复用个人主页的静屿使用指南数据，手风琴折叠） -->
    <section class="guide-section">
      <h2 class="section-title">岛上指南</h2>
      <p class="section-subtitle">每个去处怎么玩 · 一目了然</p>
      <div class="guide-list">
        <div v-for="(s, i) in GUIDE_SECTIONS" :key="i" class="guide-card card">
          <div class="guide-card__head" @click="guideOpen = guideOpen === i ? null : i">
            <span class="guide-card__icon">{{ s.icon }}</span>
            <div class="guide-card__body">
              <div class="guide-card__title">{{ s.title }}</div>
              <div class="guide-card__desc">{{ s.desc }}</div>
            </div>
            <span class="guide-card__arrow" :class="{ 'guide-card__arrow--open': guideOpen === i }">›</span>
          </div>
          <transition name="guide-expand">
            <div v-if="guideOpen === i" class="guide-card__details">
              <p v-for="(d, j) in s.details" :key="j" class="guide-card__detail">{{ d }}</p>
            </div>
          </transition>
        </div>
      </div>
    </section>

    <!-- 未登录引导 -->
    <section v-if="!userStore.isLoggedIn" class="guest-cta card">
      <h3 class="guest-cta__title">第一次来静屿？</h3>
      <p class="guest-cta__desc">注册一个只属于你的小岛空间</p>
      <div class="guest-cta__btns">
        <router-link to="/register" class="btn btn--primary">开启我的岛</router-link>
        <router-link to="/login" class="btn btn--ghost">已有账号</router-link>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  max-width: 1100px;
  margin: 0 auto;
}

/* Hero：3D 场景 + 文字叠加 */
.hero {
  position: relative;
  min-height: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 16px 0 0;
  border-radius: var(--radius-xl, 32px);
  overflow: hidden;
  box-shadow: var(--shadow-lg, 0 12px 40px rgba(139, 123, 94, 0.15));
}
.hero__scene {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}
.hero__content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 56px;
  width: 100%;
  padding: 60px 48px;
}
/* 左侧品牌（🌊 + slogan + 大字），保留原文字投影保证雾海上可读 */
.hero__brand {
  text-align: center;
  text-shadow: 0 2px 12px rgba(249, 246, 240, 0.6),
               0 0 32px rgba(249, 246, 240, 0.4);
}
/* v2.5.0：右侧理念卡（毛玻璃半透明，心灵港湾定位 + 信任点） */
.hero__intro {
  max-width: 320px;
  padding: 26px 28px;
  border-radius: var(--radius-lg, 20px);
  background: rgba(249, 246, 240, 0.78);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 8px 32px rgba(139, 123, 94, 0.12);
  text-align: left;
}
.hero__intro-lead {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: 0.08em;
  margin: 0 0 12px;
}
.hero__intro-body {
  font-size: 13.5px;
  line-height: 2;
  color: var(--color-text-secondary);
  margin: 0 0 14px;
}
.hero__intro-trust {
  font-size: 11.5px;
  color: var(--color-text-muted);
  letter-spacing: 0.05em;
  margin: 0;
  padding-top: 12px;
  border-top: 1px dashed rgba(139, 123, 94, 0.25);
}
.hero-icon {
  font-size: 56px;
  display: inline-block;
  margin-bottom: 16px;
  filter: drop-shadow(0 4px 12px rgba(168, 197, 232, 0.5));
}
.hero-verse {
  font-family: var(--font-serif);
  font-size: 15px;
  color: var(--color-text-secondary);
  font-style: italic;
  margin-bottom: 16px;
  letter-spacing: 0.1em;
}
.hero-title {
  font-family: var(--font-serif);
  font-size: clamp(48px, 8vw, 80px);
  font-weight: 400;
  letter-spacing: 0.2em;
  color: var(--color-text-primary);
  margin: 0;
}

/* 向下滚动提示（可点击） */
.hero__scroll-hint {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  font-family: var(--font-serif);
  font-size: 12px;
  color: var(--color-text-muted);
  letter-spacing: 0.15em;
  cursor: pointer;
  animation: scrollHint 2.4s ease-in-out infinite;
  transition: color 0.3s var(--ease-apple), opacity 0.3s var(--ease-apple);
}
.hero__scroll-hint:hover {
  color: var(--color-accent-dark);
  opacity: 1;
}
.hero__scroll-arrow {
  font-size: 14px;
}
@keyframes scrollHint {
  0%, 100% { transform: translateX(-50%) translateY(0); opacity: 0.55; }
  50% { transform: translateX(-50%) translateY(4px); opacity: 0.85; }
}

/* Section 通用 */
.section-title {
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 400;
  letter-spacing: 0.15em;
  color: var(--color-text-primary);
  text-align: center;
  margin: 0 0 8px;
}
.section-subtitle {
  text-align: center;
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 32px;
  letter-spacing: 0.1em;
}

/* 模块入口 */
.module-section {
  margin: 60px 0;
}
.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}
.module-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px 24px;
  text-align: left;
  transition: transform 0.4s var(--ease-apple), box-shadow 0.4s var(--ease-apple);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transform-style: preserve-3d;
  will-change: transform;
}
.module-card:hover {
  box-shadow: var(--shadow-md);
  color: var(--color-text-primary);
}
.module-card__icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 28px;
  flex-shrink: 0;
  transform: translateZ(12px);
}
.module-card__body {
  flex: 1;
  min-width: 0;
  transform: translateZ(6px);
}
.module-card__title {
  font-family: var(--font-serif);
  font-size: 19px;
  font-weight: 500;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}
.module-card__desc {
  font-size: 12.5px;
  color: var(--color-text-muted);
  line-height: 1.5;
}
/* v2.5.0：「怎么玩」奖励行 */
.module-card__reward {
  margin-top: 6px;
  font-size: 11px;
  color: var(--color-text-muted);
  opacity: 0.85;
  line-height: 1.5;
  letter-spacing: 0.02em;
}
.module-card:hover .module-card__reward {
  color: var(--color-accent-dark);
  opacity: 1;
}
.module-card__arrow {
  color: var(--color-text-muted);
  font-size: 18px;
  flex-shrink: 0;
  transition: transform 0.3s var(--ease-apple);
  transform: translateZ(8px);
}
.module-card:hover .module-card__arrow {
  transform: translateX(4px) translateZ(8px);
  color: var(--color-accent-dark);
}

/* 未登录引导 */
.guest-cta {
  text-align: center;
  padding: 40px 28px;
  margin: 60px 0;
}
.guest-cta__title {
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 400;
  margin: 0 0 8px;
  letter-spacing: 0.1em;
}
.guest-cta__desc {
  color: var(--color-text-muted);
  margin: 0 0 24px;
}
.guest-cta__btns {
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* ── 岛上指南（v2.5.0：与个人主页同款手风琴）── */
.guide-section {
  margin: 60px 0 0;
}
.guide-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 760px;
  margin: 0 auto;
}
.guide-card {
  padding: 0;
  overflow: hidden;
}
.guide-card__head {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  cursor: pointer;
  transition: background 0.2s;
}
.guide-card__head:hover {
  background: rgba(184, 165, 144, 0.06);
}
.guide-card__icon {
  font-size: 28px;
  flex-shrink: 0;
}
.guide-card__body {
  flex: 1;
  min-width: 0;
}
.guide-card__title {
  font-family: var(--font-serif, serif);
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 2px;
  letter-spacing: 0.05em;
}
.guide-card__desc {
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.5;
}
.guide-card__arrow {
  font-size: 20px;
  color: var(--color-text-muted);
  transition: transform 0.3s var(--ease-soft, ease);
  flex-shrink: 0;
}
.guide-card__arrow--open {
  transform: rotate(90deg);
}
.guide-card__details {
  padding: 0 20px 18px 62px;
}
.guide-card__detail {
  font-size: 12.5px;
  line-height: 1.8;
  color: var(--color-text-secondary);
  margin: 0 0 4px;
  position: relative;
  padding-left: 14px;
}
.guide-card__detail::before {
  content: '·';
  position: absolute;
  left: 0;
  color: var(--color-text-muted);
}
.guide-expand-enter-active,
.guide-expand-leave-active {
  transition: all 0.3s var(--ease-soft, ease);
  overflow: hidden;
}
.guide-expand-enter-from,
.guide-expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.guide-expand-enter-to,
.guide-expand-leave-from {
  max-height: 500px;
}

/* 响应式：三档断点（手机 ≤768 / 平板 769-1024 / 桌面 ≥1025） */

/* ── 平板（769-1024px）：紧凑布局 ── */
@media (min-width: 769px) and (max-width: 1024px) {
  .home {
    max-width: 960px;
  }
  .hero {
    min-height: 440px;
    margin: 12px 0 0;
  }
  .hero__content {
    padding: 48px 20px;
    gap: 32px;
  }
  .hero__intro {
    max-width: 280px;
    padding: 22px 24px;
  }
  .hero-icon {
    font-size: 48px;
  }
  .hero-title {
    font-size: clamp(44px, 7vw, 64px);
  }
  .module-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
  }
  .module-card {
    padding: 18px 20px;
  }
  .guest-cta__btns {
    flex-wrap: wrap;
  }
}

/* ── 移动端（≤768px）：手机竖屏，差异化布局 ── */
@media (max-width: 768px) {
  .home {
    max-width: 100%;
    padding: 0 12px;
  }
  .hero {
    min-height: 380px;
    min-height: min(380px, 60svh);
    margin: 8px 0 0;
    border-radius: var(--radius-lg, 20px);
  }
  .hero__content {
    flex-direction: column;
    gap: 22px;
    padding: 32px 16px;
  }
  .hero__intro {
    max-width: 100%;
    width: 100%;
    padding: 20px 22px;
    text-align: center;
  }
  .hero__intro-lead {
    font-size: 15px;
  }
  .hero__intro-body {
    font-size: 12.5px;
    line-height: 1.9;
  }
  .hero__intro-trust {
    font-size: 10.5px;
    padding-top: 10px;
  }
  .hero-icon {
    font-size: 40px;
    margin-bottom: 10px;
  }
  .hero-verse {
    font-size: 13px;
    margin-bottom: 10px;
  }
  .hero-title {
    font-size: clamp(36px, 11vw, 52px);
    margin: 0 0 12px;
  }
  .hero__scroll-hint {
    bottom: 12px;
    font-size: 11px;
  }

  .section-title {
    font-size: 20px;
  }
  .section-subtitle {
    font-size: 12px;
    margin-bottom: 20px;
  }

  /* 模块入口：单列大卡片，移动端展示更详细信息 */
  .module-section {
    margin: 32px 0;
  }
  .module-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .module-card {
    padding: 16px 18px;
    gap: 14px;
  }
  .module-card__icon {
    width: 48px;
    height: 48px;
    font-size: 24px;
  }
  .module-card__title {
    font-size: 17px;
    margin-bottom: 2px;
  }
  .module-card__desc {
    font-size: 12px;
  }

  /* 未登录引导：紧凑 */
  .guest-cta {
    padding: 28px 20px;
    margin: 32px 0;
  }

  /* 岛上指南：紧凑，明细缩进改平铺 */
  .guide-section {
    margin: 32px 0 0;
  }
  .guide-list {
    gap: 10px;
  }
  .guide-card__head {
    padding: 14px 16px;
    gap: 12px;
  }
  .guide-card__icon {
    font-size: 24px;
  }
  .guide-card__details {
    padding: 0 16px 14px 16px;
  }
  .guest-cta__title {
    font-size: 19px;
  }
  .guest-cta__desc {
    font-size: 13px;
    margin: 0 0 18px;
  }
  .guest-cta__btns {
    flex-direction: column;
    gap: 8px;
  }
  .guest-cta__btns .btn {
    width: 100%;
  }
}

/* reduced-motion：关 3D 倾斜 + 关滚动提示动画 */
@media (prefers-reduced-motion: reduce) {
  .module-card {
    transition: box-shadow 0.4s;
  }
  .hero__scroll-hint {
    animation: none;
    opacity: 0.5;
  }
}
</style>
