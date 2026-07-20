<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'
import { useUserStore } from '@/stores/user'

// 异步加载 Three.js 花田组件（按需加载，减小首屏包）
const FlowerField = defineAsyncComponent(() =>
  import('@/components/FlowerField.vue')
)

const router = useRouter()
const userStore = useUserStore()

// 物品类型映射（前端展示用）
const ITEM_TYPE_INFO = {
  plant: { label: '植物', color: '#A8C5A0' },
  flower: { label: '花卉', color: '#E8B8C5' },
  stone: { label: '石头', color: '#B8A590' },
  ornament: { label: '装饰', color: '#A8B8C5' },
  badge: { label: '徽章', color: '#E8C5A8' },
}

// 数据
const myItems = ref([])
const energyRecords = ref([])
const energySummary = ref({ total_energy: 0, by_source: {} })
const loading = ref(false)

// 简易 toast
const toastVisible = ref(false)
const toastText = ref('')
let toastTimer = null
const showToast = (text, duration = 2500) => {
  toastText.value = text
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, duration)
}

// 我的能量（从 userStore 取，刷新时用 summary 同步）
const myEnergy = computed(() => userStore.energy)

// 按物品类型分组
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

// 能量来源标签
const SOURCE_LABEL = {
  music: '聆听音乐',
  diary: '写下日记',
  mood: '心情打卡',
  bottle: '拾起漂流瓶',
  encouragement: '收到鼓励',
  ai: 'AI 树洞',
  exchange: '兑换物品',
  achievement: '获得成就',
}

const sourceBars = computed(() => {
  const entries = Object.entries(energySummary.value.by_source || {})
  const max = Math.max(1, ...entries.map(([, v]) => v))
  return entries
    .map(([source, value]) => ({
      source,
      label: SOURCE_LABEL[source] || source,
      value,
      widthPct: Math.max(4, (value / max) * 100),
    }))
    .sort((a, b) => b.value - a.value)
})

// 格式化日期
const formatDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

const formatDateTime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${d.getMonth() + 1}月${d.getDate()}日 ${h}:${m}`
}

// 拉取数据
const fetchAll = async () => {
  loading.value = true
  try {
    const [mine, summary, records] = await Promise.all([
      api.get('/garden/mine'),
      api.get('/energy/summary'),
      api.get('/energy/records', { params: { limit: 30 } }),
    ])
    myItems.value = mine?.items || []
    energySummary.value = summary || { total_energy: 0, by_source: {} }
    energyRecords.value = records || []
    // 同步能量到 store
    if (typeof summary?.total_energy === 'number') {
      userStore.updateEnergy(summary.total_energy)
    }
    // 数据加载完，等 DOM 更新后再触发入场动画
    await nextTick()
    playEnterAnimations()
  } catch (e) {
    showToast(e.message || '花园加载失败', 2500)
  } finally {
    loading.value = false
  }
}

// 入场动画：对每个选择器先检查存在再调 gsap，避免 GSAP "target not found" 警告
const playEnterAnimations = () => {
  gsap.from('.garden-header', { y: -20, opacity: 0, duration: 0.6, ease: 'power2.out' })
  gsap.from('.energy-card', { y: 20, opacity: 0, duration: 0.6, ease: 'power3.out', delay: 0.1 })
  if (document.querySelector('.source-bar')) {
    gsap.from('.source-bar', {
      scaleX: 0, transformOrigin: 'left', duration: 0.55, stagger: 0.06, ease: 'power2.out', delay: 0.3,
    })
  }
  if (document.querySelector('.garden-item')) {
    gsap.from('.garden-item', {
      y: 16, opacity: 0, duration: 0.45, stagger: 0.05, ease: 'power2.out', delay: 0.4,
    })
  }
  if (document.querySelector('.record-row')) {
    gsap.from('.record-row', {
      x: -10, opacity: 0, duration: 0.4, stagger: 0.04, ease: 'power2.out', delay: 0.6,
    })
  }
}

const goShop = () => router.push('/shop')

onMounted(() => {
  fetchAll()
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="garden-view">
    <!-- 顶部标题 -->
    <header class="garden-header">
      <h1 class="garden-header__title">精神花园</h1>
      <p class="garden-header__verse">"每一份静默的耕耘，都会在某处开花"</p>
    </header>

    <!-- 3D 花田场景（异步加载 Three.js） -->
    <section class="garden-hero">
      <FlowerField :flower-count="60" height="380px" />
      <div class="garden-hero__overlay">
        <p class="garden-hero__hint">移动鼠标，看花田随风摆动</p>
      </div>
    </section>

    <!-- 能量卡 -->
    <section class="energy-card card">
      <div class="energy-card__head">
        <div class="energy-card__label">露水能量</div>
        <div class="energy-card__value">
          <span class="energy-card__icon">💧</span>
          <span class="energy-card__num">{{ myEnergy }}</span>
        </div>
      </div>
      <button class="btn btn--primary energy-card__cta" @click="goShop">
        去商店兑换 →
      </button>
    </section>

    <!-- 能量来源分布 -->
    <section class="source-section card" v-if="sourceBars.length">
      <h2 class="section-title">能量来源</h2>
      <p class="section-subtitle">这些是你在静屿里收集到的光</p>
      <div class="source-list">
        <div v-for="(s, i) in sourceBars" :key="i" class="source-row">
          <div class="source-row__label">{{ s.label }}</div>
          <div class="source-row__bar">
            <div class="source-bar" :style="{ width: s.widthPct + '%' }"></div>
          </div>
          <div class="source-row__value">+{{ s.value }}</div>
        </div>
      </div>
    </section>

    <!-- 我的花园物品 -->
    <section class="items-section">
      <div class="items-section__head">
        <h2 class="section-title">我的花园</h2>
        <span class="items-section__count">{{ myItems.length }} 件</span>
      </div>

      <div v-if="loading && !myItems.length" class="items-empty">正在拾起散落的花…</div>
      <div v-else-if="!myItems.length" class="items-empty">
        花园还空着，去商店兑换一些植物种下吧 🌱
      </div>

      <div v-else class="items-groups">
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
              class="garden-item card"
              :title="item.description || item.name"
            >
              <div class="garden-item__emoji">{{ item.image }}</div>
              <div class="garden-item__name">{{ item.name }}</div>
              <div class="garden-item__date">{{ formatDate(item.obtained_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 能量流水 -->
    <section class="records-section card" v-if="energyRecords.length">
      <h2 class="section-title">能量流水</h2>
      <p class="section-subtitle">最近 30 条</p>
      <div class="records-list">
        <div
          v-for="(r, i) in energyRecords"
          :key="r.id || i"
          class="record-row"
        >
          <div class="record-row__main">
            <div class="record-row__source">{{ SOURCE_LABEL[r.source] || r.source }}</div>
            <div class="record-row__note" v-if="r.note">{{ r.note }}</div>
            <div class="record-row__time">{{ formatDateTime(r.created_at) }}</div>
          </div>
          <div class="record-row__amount" :class="{ 'is-positive': r.amount > 0, 'is-negative': r.amount < 0 }">
            {{ r.amount > 0 ? '+' : '' }}{{ r.amount }}
          </div>
        </div>
      </div>
    </section>

    <!-- toast -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.garden-view {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* 标题 */
.garden-header {
  text-align: center;
  margin-bottom: 28px;
}
.garden-header__title {
  font-family: var(--font-serif, serif);
  font-size: 30px;
  font-weight: 500;
  letter-spacing: 0.1em;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
}
.garden-header__verse {
  font-family: var(--font-serif, serif);
  font-style: italic;
  font-size: 14px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
  letter-spacing: 0.05em;
}

/* 3D 花田场景 */
.garden-hero {
  position: relative;
  margin-bottom: 28px;
  border-radius: var(--radius-lg, 20px);
  overflow: hidden;
  box-shadow: var(--shadow-md, 0 4px 12px rgba(74, 68, 56, 0.08));
}
.garden-hero__overlay {
  position: absolute;
  bottom: 12px;
  left: 0;
  right: 0;
  text-align: center;
  pointer-events: none;
  z-index: 3;
}
.garden-hero__hint {
  display: inline-block;
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  font-family: var(--font-serif, serif);
  font-size: 12px;
  color: var(--color-text-secondary, #5C4F3E);
  letter-spacing: 0.05em;
}

/* 通用 section 标题 */
.section-title {
  font-family: var(--font-serif, serif);
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
  letter-spacing: 0.05em;
}
.section-subtitle {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0 0 18px;
}

/* 能量卡 */
.energy-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px;
  margin-bottom: 28px;
  background: linear-gradient(135deg, rgba(168, 197, 232, 0.18) 0%, rgba(232, 184, 197, 0.18) 100%);
}
.energy-card__label {
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--color-text-secondary, #5C4F3E);
  letter-spacing: 0.08em;
  margin-bottom: 6px;
}
.energy-card__value {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.energy-card__icon {
  font-size: 26px;
}
.energy-card__num {
  font-family: var(--font-serif, serif);
  font-size: 38px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  letter-spacing: 0.02em;
}
.energy-card__cta {
  min-width: 140px;
}

/* 能量来源 */
.source-section {
  padding: 24px;
  margin-bottom: 36px;
}
.source-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.source-row {
  display: flex;
  align-items: center;
  gap: 14px;
}
.source-row__label {
  flex: 0 0 96px;
  font-size: 13px;
  color: var(--color-text-secondary, #5C4F3E);
  font-family: var(--font-serif, serif);
}
.source-row__bar {
  flex: 1;
  height: 10px;
  background: rgba(139, 123, 94, 0.1);
  border-radius: 5px;
  overflow: hidden;
}
.source-bar {
  height: 100%;
  background: linear-gradient(90deg, #A8C5A0 0%, #93B58B 100%);
  border-radius: 5px;
  transition: width 0.5s var(--ease-soft, ease);
}
.source-row__value {
  flex: 0 0 60px;
  text-align: right;
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--color-text-primary, #3D3327);
}

/* 我的花园 */
.items-section {
  margin-bottom: 36px;
}
.items-section__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 16px;
}
.items-section__count {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  font-family: var(--font-serif, serif);
}
.items-empty {
  text-align: center;
  padding: 36px 20px;
  color: var(--color-text-muted, #8B7B5E);
  font-size: 14px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-lg, 20px);
}
.items-groups {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.item-group__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-serif, serif);
  font-size: 15px;
  color: var(--color-text-secondary, #5C4F3E);
  margin-bottom: 12px;
  letter-spacing: 0.05em;
}
.item-group__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.item-group__count {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  margin-left: 4px;
}
.item-group__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 14px;
}
.garden-item {
  padding: 16px 12px;
  text-align: center;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 246, 240, 0.85) 100%);
  transition: transform 0.25s var(--ease-soft, ease), box-shadow 0.25s;
}
.garden-item:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.1));
}
.garden-item__emoji {
  font-size: 36px;
  line-height: 1;
  margin-bottom: 8px;
}
.garden-item__name {
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 4px;
  letter-spacing: 0.03em;
}
.garden-item__date {
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
}

/* 能量流水 */
.records-section {
  padding: 24px;
}
.records-list {
  display: flex;
  flex-direction: column;
}
.record-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border, rgba(139, 123, 94, 0.1));
}
.record-row:last-child {
  border-bottom: none;
}
.record-row__source {
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--color-text-primary, #3D3327);
}
.record-row__note {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  margin-top: 2px;
}
.record-row__time {
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  margin-top: 2px;
}
.record-row__amount {
  font-family: var(--font-serif, serif);
  font-size: 16px;
  font-weight: 500;
}
.record-row__amount.is-positive {
  color: #93B58B;
}
.record-row__amount.is-negative {
  color: #C97064;
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

/* 响应式 */
@media (max-width: 640px) {
  .garden-view {
    padding: 20px 14px 60px;
  }
  .garden-header__title {
    font-size: 24px;
  }
  .energy-card {
    flex-direction: column;
    gap: 16px;
    padding: 20px 18px;
    text-align: center;
  }
  .energy-card__cta {
    width: 100%;
  }
  .source-row__label {
    flex: 0 0 76px;
    font-size: 12px;
  }
  .source-row__value {
    flex: 0 0 44px;
    font-size: 13px;
  }
  .item-group__grid {
    grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
    gap: 10px;
  }
  .garden-item__emoji {
    font-size: 30px;
  }
  .garden-item__name {
    font-size: 13px;
  }
}
</style>
