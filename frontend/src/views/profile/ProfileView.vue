<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 数据
const profile = ref(null)
const myItems = ref([])
const flowers = ref([])
const loading = ref(false)
const errorMsg = ref('')

// 简易 toast
const toastVisible = ref(false)
const toastText = ref('')
let toastTimer = null
const showToast = (text) => {
  toastText.value = text
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, 2200)
}

// 日期格式化
const formatDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

// 注册天数
const daysOnIsland = computed(() => {
  if (!profile.value?.created_at) return 0
  const d = new Date(profile.value.created_at)
  if (isNaN(d.getTime())) return 0
  const diff = Date.now() - d.getTime()
  return Math.max(1, Math.floor(diff / (24 * 60 * 60 * 1000)) + 1)
})

// 物品类型映射
const ITEM_TYPE_INFO = {
  costume: { label: '装扮', color: '#A8B8C5' },
  badge:   { label: '徽章', color: '#E8C5A8' },
}

const groupedItems = computed(() => {
  const groups = {}
  myItems.value.forEach(item => {
    const type = item.item_type || 'other'
    if (!groups[type]) groups[type] = []
    groups[type].push(item)
  })
  return Object.entries(groups).map(([type, items]) => ({
    type,
    label: ITEM_TYPE_INFO[type]?.label || type,
    color: ITEM_TYPE_INFO[type]?.color || '#B8A590',
    items,
  }))
})

// 花朵生长阶段
const STAGE_INFO = {
  seed:   { label: '种子', emoji: '🌱', color: '#A8C5A0' },
  sprout: { label: '发芽', emoji: '🌿', color: '#7FB069' },
  bud:    { label: '花苞', emoji: '🥀', color: '#E8B8C5' },
  bloom:  { label: '盛开', emoji: '🌸', color: '#F5A8C5' },
  wilted: { label: '枯萎', emoji: '🍂', color: '#B8A590' },
}

const flowerStats = computed(() => {
  const total = flowers.value.length
  const bloom = flowers.value.filter(f => f.stage === 'bloom').length
  const wilted = flowers.value.filter(f => f.stage === 'wilted').length
  return { total, bloom, wilted }
})

// 拉取主页数据
const fetchProfile = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const [p, mine, fls] = await Promise.all([
      api.get('/profile'),
      api.get('/garden/mine').catch(() => ({ items: [] })),
      api.get('/garden/flowers').catch(() => ({ items: [] })),
    ])
    profile.value = p
    myItems.value = mine?.items || []
    flowers.value = fls?.items || []
    // 同步本地 store 的资源
    if (typeof p?.total_energy === 'number') {
      userStore.updateResources({
        total_energy: p.total_energy,
        leaves: p.leaves,
      })
    }
    await nextTick()
    playEnterAnimations()
  } catch (e) {
    errorMsg.value = e.message || '主页加载失败'
  } finally {
    loading.value = false
  }
}

const playEnterAnimations = () => {
  gsap.from('.profile-hero', { y: -20, opacity: 0, duration: 0.6, ease: 'power2.out' })
  gsap.from('.stat-card', {
    y: 18, opacity: 0, duration: 0.5, stagger: 0.06, ease: 'power3.out', delay: 0.1,
  })
  if (document.querySelector('.badge-card')) {
    gsap.from('.badge-card', {
      y: 14, opacity: 0, duration: 0.45, stagger: 0.06, ease: 'power2.out', delay: 0.3,
    })
  }
}

// 跳转
const goNotifications = () => router.push('/notifications')
const goGarden = () => router.push('/garden')
const goShop = () => router.push('/shop')
const goDiary = () => router.push('/diary')
const goCalendar = () => router.push('/calendar')
const goMusic = () => router.push('/music')
const goAiChat = () => router.push('/ai-chat')

const handleLogout = async () => {
  await userStore.logout()
  router.push('/')
}

onMounted(() => {
  fetchProfile()
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="profile-view">
    <!-- 顶部个人卡 -->
    <header class="profile-hero card">
      <div class="profile-hero__avatar">🏝️</div>
      <div class="profile-hero__body">
        <h1 class="profile-hero__name">{{ profile?.nickname || userStore.nickname || '岛主' }}</h1>
        <p class="profile-hero__meta">
          在静屿的第 <strong>{{ daysOnIsland }}</strong> 天
          <span v-if="profile?.is_admin" class="profile-hero__admin">· 管理员</span>
        </p>
        <p class="profile-hero__date" v-if="profile?.created_at">
          登岛于 {{ formatDate(profile.created_at) }}
        </p>
      </div>
      <div class="profile-hero__actions">
        <button class="btn btn--ghost profile-hero__btn" @click="goNotifications">🔔 通知</button>
        <button class="btn btn--ghost profile-hero__btn profile-hero__btn--logout" @click="handleLogout">离开</button>
      </div>
    </header>

    <!-- 加载/错误 -->
    <div v-if="loading && !profile" class="empty-state card">正在拾起散落的回忆…</div>
    <div v-else-if="errorMsg && !profile" class="empty-state card">{{ errorMsg }}</div>

    <template v-if="profile">
      <!-- 双资源条 -->
      <section class="resource-grid">
        <div class="resource-card card">
          <div class="resource-card__head">
            <div class="resource-card__label">露水</div>
            <div class="resource-card__icon">💧</div>
          </div>
          <div class="resource-card__value">{{ profile.total_energy }}</div>
          <div class="resource-card__hint">浇灌花朵盛开</div>
        </div>
        <div class="resource-card card">
          <div class="resource-card__head">
            <div class="resource-card__label">落叶</div>
            <div class="resource-card__icon">🍂</div>
          </div>
          <div class="resource-card__value">{{ profile.leaves }}</div>
          <div class="resource-card__hint">兑换花种</div>
        </div>
      </section>

      <!-- 统计 -->
      <section class="stats-section">
        <h2 class="section-title">岛上足迹</h2>
        <div class="stat-grid">
          <button class="stat-card card" @click="goDiary">
            <div class="stat-card__emoji">📖</div>
            <div class="stat-card__num">{{ profile.stats.diary_count }}</div>
            <div class="stat-card__label">日记</div>
            <div class="stat-card__sub" v-if="profile.stats.public_diary_count">
              公开 {{ profile.stats.public_diary_count }}
            </div>
          </button>
          <button class="stat-card card" @click="goCalendar">
            <div class="stat-card__emoji">🌙</div>
            <div class="stat-card__num">{{ profile.stats.checkin_count }}</div>
            <div class="stat-card__label">打卡</div>
            <div class="stat-card__sub">连续 {{ profile.stats.streak }} 天</div>
          </button>
          <button class="stat-card card" @click="goMusic">
            <div class="stat-card__emoji">🎵</div>
            <div class="stat-card__num">{{ profile.stats.listen_count }}</div>
            <div class="stat-card__label">听曲</div>
            <div class="stat-card__sub">古琴疗愈</div>
          </button>
          <button class="stat-card card" @click="goGarden">
            <div class="stat-card__emoji">🌸</div>
            <div class="stat-card__num">{{ flowerStats.total }}</div>
            <div class="stat-card__label">花朵</div>
            <div class="stat-card__sub">盛开 {{ flowerStats.bloom }}</div>
          </button>
          <div class="stat-card card">
            <div class="stat-card__emoji">💛</div>
            <div class="stat-card__num">{{ profile.stats.received_encouragement_count }}</div>
            <div class="stat-card__label">收到鼓励</div>
            <div class="stat-card__sub">来自漂流瓶</div>
          </div>
          <div class="stat-card card">
            <div class="stat-card__emoji">🎁</div>
            <div class="stat-card__num">{{ profile.stats.garden_item_count }}</div>
            <div class="stat-card__label">岛上物件</div>
            <div class="stat-card__sub">装扮/徽章</div>
          </div>
        </div>
      </section>

      <!-- 快捷入口 -->
      <section class="quick-section">
        <h2 class="section-title">前往各处</h2>
        <div class="quick-grid">
          <button class="quick-card card" @click="goGarden">
            <span class="quick-card__emoji">🌸</span>
            <span class="quick-card__label">屿上花田</span>
          </button>
          <button class="quick-card card" @click="goShop">
            <span class="quick-card__emoji">🍂</span>
            <span class="quick-card__label">落叶画坊</span>
          </button>
          <button class="quick-card card" @click="goDiary">
            <span class="quick-card__emoji">📖</span>
            <span class="quick-card__label">日记海岸</span>
          </button>
          <button class="quick-card card" @click="goCalendar">
            <span class="quick-card__emoji">🌙</span>
            <span class="quick-card__label">情绪日历</span>
          </button>
          <button class="quick-card card" @click="goMusic">
            <span class="quick-card__emoji">🎵</span>
            <span class="quick-card__label">琴音疗心</span>
          </button>
          <button class="quick-card card" @click="goAiChat">
            <span class="quick-card__emoji">🌳</span>
            <span class="quick-card__label">心语树洞</span>
          </button>
        </div>
      </section>

      <!-- 我的物件 -->
      <section class="items-section" v-if="myItems.length">
        <h2 class="section-title">岛上物件 · {{ myItems.length }}</h2>
        <div class="items-groups">
          <div v-for="g in groupedItems" :key="g.type" class="item-group">
            <div class="item-group__title">
              <span class="item-group__dot" :style="{ background: g.color }"></span>
              {{ g.label }}
              <span class="item-group__count">×{{ g.items.length }}</span>
            </div>
            <div class="item-group__grid">
              <div
                v-for="item in g.items"
                :key="item.id"
                class="badge-card card"
                :title="item.description || item.name"
              >
                <div class="badge-card__emoji">{{ item.image }}</div>
                <div class="badge-card__name">{{ item.name }}</div>
                <div class="badge-card__date">{{ formatDate(item.obtained_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 我的花朵（精简展示） -->
      <section class="flowers-section" v-if="flowers.length">
        <h2 class="section-title">我的花朵 · {{ flowers.length }}</h2>
        <div class="flower-grid">
          <div
            v-for="f in flowers.slice(0, 12)"
            :key="f.id"
            class="flower-mini"
            :title="`${f.flower_type} · ${STAGE_INFO[f.stage]?.label || ''}`"
          >
            <div class="flower-mini__emoji">{{ STAGE_INFO[f.stage]?.emoji || '🌱' }}</div>
            <div class="flower-mini__name">{{ f.flower_type }}</div>
            <div class="flower-mini__stage">{{ STAGE_INFO[f.stage]?.label || f.stage }}</div>
          </div>
        </div>
        <button v-if="flowers.length > 12" class="btn btn--ghost flower-more" @click="goGarden">
          查看全部 →
        </button>
      </section>

      <!-- 空岛提示 -->
      <section v-if="!myItems.length && !flowers.length && !profile.stats.diary_count" class="empty-island card">
        <div class="empty-island__emoji">🏝️</div>
        <p class="empty-island__text">
          你的小岛还很安静，<br>
          去写一篇日记、听一曲古琴，或种下一朵花吧。
        </p>
        <button class="btn btn--primary" @click="goDiary">写一篇日记</button>
      </section>
    </template>

    <!-- toast -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.profile-view {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* 平板紧凑 */
@media (min-width: 769px) and (max-width: 1024px) {
  .profile-view {
    padding: 28px 20px 72px;
  }
  .stat-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .item-group__grid {
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  }
}

/* Hero */
.profile-hero {
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 24px 28px;
  margin-bottom: 22px;
  background: linear-gradient(135deg, rgba(168, 197, 232, 0.18) 0%, rgba(232, 184, 168, 0.18) 100%);
}
.profile-hero__avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.85), rgba(249, 246, 240, 0.9));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  flex-shrink: 0;
  box-shadow: 0 6px 20px rgba(139, 123, 94, 0.12);
}
.profile-hero__body {
  flex: 1;
  min-width: 0;
}
.profile-hero__name {
  font-family: var(--font-serif, serif);
  font-size: 26px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
  letter-spacing: 0.08em;
}
.profile-hero__meta {
  font-size: 13px;
  color: var(--color-text-secondary, #5C4F3E);
  margin: 0 0 2px;
}
.profile-hero__meta strong {
  color: var(--color-text-primary, #3D3327);
  font-weight: 500;
}
.profile-hero__admin {
  font-size: 11px;
  color: #C5946B;
  letter-spacing: 0.05em;
}
.profile-hero__date {
  font-size: 11.5px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
}
.profile-hero__actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}
.profile-hero__btn {
  white-space: nowrap;
  padding: 7px 14px;
  font-size: 12px;
}
.profile-hero__btn--logout {
  color: #C57878;
  border-color: rgba(197, 120, 120, 0.25);
}

/* 资源卡 */
.resource-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin-bottom: 28px;
}
.resource-card {
  padding: 18px 22px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 246, 240, 0.85) 100%);
}
.resource-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.resource-card__label {
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.08em;
}
.resource-card__icon {
  font-size: 22px;
}
.resource-card__value {
  font-family: var(--font-serif, serif);
  font-size: 32px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  letter-spacing: 0.02em;
  line-height: 1.1;
  margin-bottom: 4px;
}
.resource-card__hint {
  font-size: 11.5px;
  color: var(--color-text-muted, #8B7B5E);
}

/* Section 标题 */
.section-title {
  font-family: var(--font-serif, serif);
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 14px;
  letter-spacing: 0.08em;
}

/* 统计网格 */
.stats-section {
  margin-bottom: 32px;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 14px;
}
.stat-card {
  padding: 18px 14px;
  text-align: center;
  cursor: pointer;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 246, 240, 0.85) 100%);
  border: none;
  font-family: inherit;
  transition: transform 0.25s var(--ease-soft, ease), box-shadow 0.25s;
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.12));
}
.stat-card__emoji {
  font-size: 26px;
  line-height: 1;
  margin-bottom: 6px;
}
.stat-card__num {
  font-family: var(--font-serif, serif);
  font-size: 26px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  line-height: 1.1;
  margin-bottom: 2px;
}
.stat-card__label {
  font-size: 12px;
  color: var(--color-text-secondary, #5C4F3E);
  letter-spacing: 0.05em;
}
.stat-card__sub {
  font-size: 10.5px;
  color: var(--color-text-muted, #8B7B5E);
  margin-top: 4px;
}

/* 快捷入口 */
.quick-section {
  margin-bottom: 32px;
}
.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 12px;
}
.quick-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 10px;
  cursor: pointer;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 246, 240, 0.85) 100%);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  font-family: inherit;
  transition: transform 0.25s var(--ease-soft, ease), box-shadow 0.25s;
}
.quick-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.1));
}
.quick-card__emoji {
  font-size: 28px;
}
.quick-card__label {
  font-family: var(--font-serif, serif);
  font-size: 12.5px;
  color: var(--color-text-secondary, #5C4F3E);
  letter-spacing: 0.05em;
}

/* 物件 */
.items-section {
  margin-bottom: 32px;
}
.items-groups {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.item-group__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--color-text-secondary, #5C4F3E);
  margin-bottom: 10px;
  letter-spacing: 0.05em;
}
.item-group__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.item-group__count {
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  margin-left: 4px;
}
.item-group__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 12px;
}
.badge-card {
  padding: 14px 10px;
  text-align: center;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 246, 240, 0.85) 100%);
}
.badge-card__emoji {
  font-size: 30px;
  line-height: 1;
  margin-bottom: 6px;
}
.badge-card__name {
  font-family: var(--font-serif, serif);
  font-size: 12.5px;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 3px;
  letter-spacing: 0.03em;
}
.badge-card__date {
  font-size: 10.5px;
  color: var(--color-text-muted, #8B7B5E);
}

/* 花朵精简 */
.flowers-section {
  margin-bottom: 32px;
}
.flower-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(86px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.flower-mini {
  text-align: center;
  padding: 12px 6px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.7) 0%, rgba(255, 246, 240, 0.7) 100%);
  border-radius: var(--radius-md, 14px);
}
.flower-mini__emoji {
  font-size: 26px;
  line-height: 1;
  margin-bottom: 4px;
}
.flower-mini__name {
  font-family: var(--font-serif, serif);
  font-size: 11.5px;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 2px;
}
.flower-mini__stage {
  font-size: 10px;
  color: var(--color-text-muted, #8B7B5E);
}
.flower-more {
  display: block;
  margin: 0 auto;
}

/* 空岛 */
.empty-island {
  text-align: center;
  padding: 36px 24px;
  margin-top: 12px;
}
.empty-island__emoji {
  font-size: 48px;
  margin-bottom: 12px;
}
.empty-island__text {
  font-family: var(--font-serif, serif);
  font-size: 14px;
  line-height: 1.9;
  color: var(--color-text-secondary, #5C4F3E);
  margin: 0 0 18px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 36px 20px;
  color: var(--color-text-muted, #8B7B5E);
  font-size: 14px;
}

/* toast */
.toast {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(90, 70, 50, 0.92);
  color: #fff;
  padding: 12px 22px;
  border-radius: 22px;
  font-size: 14px;
  z-index: 200;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  max-width: 80%;
  text-align: center;
  line-height: 1.5;
}
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* 移动端 */
@media (max-width: 768px) {
  .profile-view {
    padding: 20px 14px 80px;
  }
  .profile-hero {
    flex-direction: column;
    text-align: center;
    padding: 22px 18px;
    gap: 14px;
  }
  .profile-hero__avatar {
    width: 64px;
    height: 64px;
    font-size: 32px;
  }
  .profile-hero__name {
    font-size: 22px;
  }
  .profile-hero__actions {
    flex-direction: row;
    width: 100%;
  }
  .profile-hero__btn {
    flex: 1;
  }
  /* 资源卡 */
  .resource-grid {
    gap: 10px;
    margin-bottom: 22px;
  }
  .resource-card {
    padding: 14px 14px;
  }
  .resource-card__value {
    font-size: 26px;
  }
  /* 统计 2 列 */
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  .stat-card {
    padding: 14px 10px;
  }
  .stat-card__num {
    font-size: 22px;
  }
  /* 快捷入口 3 列 */
  .quick-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }
  .quick-card {
    padding: 14px 6px;
  }
  .quick-card__emoji {
    font-size: 24px;
  }
  /* 物件 */
  .item-group__grid {
    grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
    gap: 10px;
  }
  .badge-card {
    padding: 10px 6px;
  }
  .badge-card__emoji {
    font-size: 24px;
  }
  /* 花朵 */
  .flower-grid {
    grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
  }
  /* toast 上移避开 tabbar */
  .toast {
    bottom: calc(90px + env(safe-area-inset-bottom));
  }
}
</style>
