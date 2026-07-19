<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { gsap } from 'gsap'

const router = useRouter()
const userStore = useUserStore()

// 五音数据
const yinList = [
  { key: 'gong', name: '宫', element: '土', organ: '脾', color: '#E8B8A8', desc: '安神厚德' },
  { key: 'shang', name: '商', element: '金', organ: '肺', color: '#E8C5A8', desc: '肃降清心' },
  { key: 'jue', name: '角', element: '木', organ: '肝', color: '#A8C5A0', desc: '疏达生发' },
  { key: 'zhi', name: '徵', element: '火', organ: '心', color: '#E8A8B8', desc: '温养喜悦' },
  { key: 'yu', name: '羽', element: '水', organ: '肾', color: '#A8B8C5', desc: '润下守静' },
]

// 模块入口
const modules = [
  { label: '漂流瓶', desc: '把心事写进瓶子，让它漂向远方', icon: '🍶', to: '/diary/pick', color: 'linear-gradient(135deg, #A8C5E8 0%, #C5D5E8 100%)' },
  { label: '情绪日历', desc: '记录每天的心情轨迹', icon: '🌙', to: '/calendar', color: 'linear-gradient(135deg, #C5C5E8 0%, #E8D5E8 100%)' },
  { label: 'AI 树洞', desc: '一个会倾听你的小岛', icon: '💭', to: '/ai-chat', color: 'linear-gradient(135deg, #B8C5E8 0%, #A8D5BA 100%)' },
  { label: '精神花园', desc: '用露水浇灌你的秘密花园', icon: '🌸', to: '/garden', color: 'linear-gradient(135deg, #E8B8C5 0%, #F5D5C5 100%)' },
]

onMounted(() => {
  // Hero 入场动效
  const tl = gsap.timeline({ delay: 0.2 })
  tl.from('.hero-verse', { y: 20, opacity: 0, duration: 1, ease: 'power3.out' })
    .from('.hero-title', { y: 30, opacity: 0, duration: 1.2, ease: 'power4.out' }, '-=0.6')
    .from('.hero-subtitle', { y: 20, opacity: 0, duration: 1, ease: 'power3.out' }, '-=0.7')
    .from('.yin-card', {
      y: 40, opacity: 0, duration: 0.8, stagger: 0.08, ease: 'power3.out'
    }, '-=0.5')
    .from('.module-card', {
      y: 30, opacity: 0, duration: 0.7, stagger: 0.06, ease: 'power3.out'
    }, '-=0.4')

  // 持续呼吸动效
  gsap.to('.hero-icon', {
    scale: 1.06, duration: 4, repeat: -1, yoyo: true, ease: 'sine.inOut'
  })
})

function goToMusic(yinKey) {
  router.push(`/music/${yinKey}`)
}
</script>

<template>
  <div class="home">
    <!-- Hero 区 -->
    <section class="hero">
      <div class="hero-icon">🌿</div>
      <p class="hero-verse">"海上有座岛，岛上有人听。"</p>
      <h1 class="hero-title">静屿</h1>
      <p class="hero-subtitle">
        古琴五音 · 漂流瓶日记 · 情绪手帐 · AI 树洞<br>
        一个属于你的治愈系身心疗愈空间
      </p>
    </section>

    <!-- 五音入口 -->
    <section class="yin-section">
      <h2 class="section-title">五音疗愈</h2>
      <p class="section-subtitle">宫商角徵羽 · 入五脏 · 调情志</p>
      <div class="yin-grid">
        <div
          v-for="yin in yinList"
          :key="yin.key"
          class="yin-card"
          :style="{ '--card-color': yin.color }"
          @click="goToMusic(yin.key)"
        >
          <div class="yin-card__char">{{ yin.name }}</div>
          <div class="yin-card__info">
            <div class="yin-card__name">{{ yin.element }}音 · 入{{ yin.organ }}</div>
            <div class="yin-card__desc">{{ yin.desc }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 今日心情条（登录后显示） -->
    <section v-if="userStore.isLoggedIn" class="today-strip card">
      <div class="today-strip__date">
        {{ new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' }) }}
      </div>
      <router-link to="/calendar" class="today-strip__action">
        今日打卡 →
      </router-link>
    </section>

    <!-- 模块入口 -->
    <section class="module-section">
      <h2 class="section-title">岛上各处</h2>
      <div class="module-grid">
        <router-link
          v-for="m in modules"
          :key="m.label"
          :to="m.to"
          class="module-card"
        >
          <div class="module-card__icon" :style="{ background: m.color }">{{ m.icon }}</div>
          <div class="module-card__title">{{ m.label }}</div>
          <div class="module-card__desc">{{ m.desc }}</div>
        </router-link>
      </div>
    </section>

    <!-- 未登录引导 -->
    <section v-if="!userStore.isLoggedIn" class="guest-cta card">
      <h3 class="guest-cta__title">第一次来静屿？</h3>
      <p class="guest-cta__desc">注册一个只属于你的小岛空间</p>
      <div class="guest-cta__btns">
        <router-link to="/register" class="btn btn--primary">开启静屿</router-link>
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

/* Hero */
.hero {
  text-align: center;
  padding: 60px 0 48px;
}
.hero-icon {
  font-size: 56px;
  display: inline-block;
  margin-bottom: 16px;
  filter: drop-shadow(0 4px 12px rgba(168, 197, 160, 0.4));
}
.hero-verse {
  font-family: var(--font-serif);
  font-size: 15px;
  color: var(--color-text-muted);
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
  margin: 0 0 20px;
}
.hero-subtitle {
  font-size: 15px;
  color: var(--color-text-secondary);
  line-height: 2;
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

/* 五音入口 */
.yin-section {
  margin: 60px 0;
}
.yin-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.yin-card {
  position: relative;
  aspect-ratio: 3/4;
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.4s var(--ease-apple);
}
.yin-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--card-color);
  opacity: 0.5;
  z-index: 0;
  transition: opacity 0.4s;
}
.yin-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%);
  z-index: 1;
  pointer-events: none;
}
.yin-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
}
.yin-card:hover::before {
  opacity: 0.75;
}
.yin-card > * {
  position: relative;
  z-index: 2;
}
.yin-card__char {
  font-family: var(--font-serif);
  font-size: 56px;
  line-height: 1;
  color: var(--color-text-primary);
  text-shadow: 0 2px 8px rgba(255, 255, 255, 0.5);
}
.yin-card__name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}
.yin-card__desc {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 今日心情条 */
.today-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 28px;
  margin: 40px 0;
  background: linear-gradient(90deg, rgba(168, 197, 160, 0.12) 0%, rgba(232, 184, 168, 0.12) 100%);
}
.today-strip__date {
  font-family: var(--font-serif);
  font-size: 17px;
  color: var(--color-text-secondary);
}
.today-strip__action {
  color: var(--color-accent-dark);
  font-weight: 500;
  transition: transform 0.3s;
}
.today-strip__action:hover {
  transform: translateX(4px);
}

/* 模块入口 */
.module-section {
  margin: 60px 0;
}
.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}
.module-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 28px 20px;
  text-align: center;
  transition: all 0.4s var(--ease-apple);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.module-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  color: var(--color-text-primary);
}
.module-card__icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 32px;
  margin-bottom: 6px;
}
.module-card__title {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 500;
}
.module-card__desc {
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.6;
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

/* 响应式 */
@media (max-width: 768px) {
  .hero { padding: 32px 0 24px; }
  .yin-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  .yin-card { aspect-ratio: 1; padding: 14px; }
  .yin-card__char { font-size: 40px; }
  .module-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .module-card { padding: 20px 14px; }
  .module-card__icon { width: 52px; height: 52px; font-size: 26px; }
  .module-card__title { font-size: 15px; }
  .module-card__desc { font-size: 12px; }
}
</style>
