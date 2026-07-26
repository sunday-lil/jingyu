<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'
import { useUserStore } from '@/stores/user'
import { isMobile } from '@/utils/visual'

// 异步加载 Three.js 花田组件（按需加载，减小首屏包）
const FlowerField = defineAsyncComponent(() =>
  import('@/components/FlowerField.vue')
)

const router = useRouter()
const userStore = useUserStore()

// 移动端降低花田花朵数（性能优化 + 兼容性）
const flowerCount = isMobile() ? 24 : 60

// 花朵生长阶段映射（与后端 STAGE_ORDER 对齐）
const STAGE_INFO = {
  seed:    { label: '种子',  emoji: '🌱', color: '#A8C5A0', progress: 0,   desc: '刚种下，等待第一缕阳光' },
  sprout:  { label: '发芽',  emoji: '🌿', color: '#7FB069', progress: 25,  desc: '冒出了嫩绿的小芽' },
  bud:     { label: '花苞',  emoji: '🥀', color: '#E8B8C5', progress: 60,  desc: '花苞紧裹，即将绽放' },
  bloom:   { label: '盛开',  emoji: '🌸', color: '#F5A8C5', progress: 100, desc: '花开正盛，被海风轻轻拂过' },
  wilted:  { label: '枯萎',  emoji: '🍂', color: '#B8A590', progress: 100, desc: '花谢了，可拾取化作落叶' },
}

// 物品类型映射（前端展示用，对应装扮/徽章）
const ITEM_TYPE_INFO = {
  costume: { label: '装扮', color: '#A8B8C5' },
  badge:   { label: '徽章', color: '#E8C5A8' },
}

// 数据
const flowers = ref([])         // 屿上花田的花朵列表（生长周期）
const myItems = ref([])          // 我持有的装扮/徽章
const loading = ref(false)
const wateringId = ref(null)     // 正在浇水的 flower_id
const collectingId = ref(null)   // 正在拾叶的 flower_id

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

// 资源：露水 + 落叶（双资源系统 v2.3）
const myEnergy = computed(() => userStore.energy)
const myLeaves = computed(() => userStore.leaves)

// 按花种分组
const groupedFlowers = computed(() => {
  const groups = {}
  flowers.value.forEach(f => {
    const type = f.flower_type || '未知'
    if (!groups[type]) groups[type] = []
    groups[type].push(f)
  })
  return Object.entries(groups).map(([type, list]) => ({
    type,
    items: list.sort((a, b) => new Date(a.planted_at) - new Date(b.planted_at)),
  }))
})

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

// 统计
const stats = computed(() => {
  const total = flowers.value.length
  const bloomed = flowers.value.filter(f => f.stage === 'bloom').length
  const wilted = flowers.value.filter(f => f.stage === 'wilted').length
  return { total, bloomed, wilted }
})

// 格式化日期
const formatDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

const formatDateTime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${d.getMonth() + 1}月${d.getDate()}日 ${h}:${m}`
}

// 拉取数据：花朵 + 持有物品
const fetchAll = async () => {
  loading.value = true
  try {
    const [flowerRes, mineRes] = await Promise.all([
      api.get('/garden/flowers'),
      api.get('/garden/mine'),
    ])
    flowers.value = flowerRes?.items || []
    myItems.value = mineRes?.items || []
    await nextTick()
    playEnterAnimations()
  } catch (e) {
    showToast(e.message || '花田加载失败', 2500)
  } finally {
    loading.value = false
  }
}

// 浇水（消耗 1 露水）
const waterFlower = async (flower) => {
  if (wateringId.value) return
  if (flower.stage === 'wilted') {
    showToast('花已枯萎，不能再浇水了 🍂')
    return
  }
  wateringId.value = flower.id
  try {
    const res = await api.post(`/garden/flowers/${flower.id}/water`)
    // 更新本地花朵状态
    const idx = flowers.value.findIndex(f => f.id === flower.id)
    if (idx > -1) {
      flowers.value[idx] = {
        ...flowers.value[idx],
        ...res,
      }
    }
    // 更新露水余额
    if (typeof res?.new_total_energy === 'number') {
      userStore.updateEnergy(res.new_total_energy)
    }
    // 提示
    const stageInfo = STAGE_INFO[res.stage]
    if (res.stage !== flower.stage) {
      showToast(`${stageInfo.emoji} 长到「${stageInfo.label}」了！`)
    } else {
      showToast(`💧 浇过水了，再浇 ${res.water_needed - res.watered_count} 次就长大`)
    }
  } catch (e) {
    showToast(e.message || '浇水失败', 2500)
  } finally {
    wateringId.value = null
  }
}

// 拾取枯花 → 转化为落叶
const collectLeaves = async (flower) => {
  if (collectingId.value) return
  if (flower.stage !== 'wilted') {
    showToast('这朵花还没枯萎，不能拾取')
    return
  }
  collectingId.value = flower.id
  try {
    const res = await api.post(`/garden/flowers/${flower.id}/collect`)
    // 从列表中移除
    flowers.value = flowers.value.filter(f => f.id !== flower.id)
    // 更新落叶数
    if (typeof res?.new_leaves === 'number') {
      userStore.updateResources({ leaves: res.new_leaves })
    }
    showToast(`🍂 拾起一朵枯花，获得 ${res.gained_leaves} 片落叶`)
  } catch (e) {
    showToast(e.message || '拾取失败', 2500)
  } finally {
    collectingId.value = null
  }
}

// 入场动画：对每个选择器先检查存在再调 gsap，避免 GSAP "target not found" 警告
const playEnterAnimations = () => {
  gsap.from('.garden-header', { y: -20, opacity: 0, duration: 0.6, ease: 'power2.out' })
  gsap.from('.resource-card', { y: 20, opacity: 0, duration: 0.6, ease: 'power3.out', delay: 0.1, stagger: 0.08 })
  if (document.querySelector('.flower-card')) {
    gsap.from('.flower-card', {
      y: 18, opacity: 0, duration: 0.5, stagger: 0.06, ease: 'power2.out', delay: 0.3,
    })
  }
  if (document.querySelector('.garden-item')) {
    gsap.from('.garden-item', {
      y: 16, opacity: 0, duration: 0.45, stagger: 0.05, ease: 'power2.out', delay: 0.5,
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
      <h1 class="garden-header__title">屿上花田</h1>
      <p class="garden-header__verse">"在静屿的土壤里，种下属于你的花"</p>
    </header>

    <!-- 3D 花田场景（异步加载 Three.js，移动端降级花朵数） -->
    <section class="garden-hero" :class="{ 'garden-hero--mobile': flowerCount === 24 }">
      <FlowerField :flower-count="flowerCount" height="360px" />
      <div class="garden-hero__overlay">
        <p class="garden-hero__hint">{{ flowerCount === 24 ? '轻触花田，看花朵绽放' : '移动鼠标，看花田随风摆动' }}</p>
      </div>
    </section>

    <!-- 双资源卡：露水 + 落叶 -->
    <section class="resource-grid">
      <div class="resource-card card">
        <div class="resource-card__head">
          <div class="resource-card__label">露水</div>
          <div class="resource-card__icon">💧</div>
        </div>
        <div class="resource-card__value">{{ myEnergy }}</div>
        <div class="resource-card__hint">用于浇灌花朵盛开</div>
      </div>
      <div class="resource-card card">
        <div class="resource-card__head">
          <div class="resource-card__label">落叶</div>
          <div class="resource-card__icon">🍂</div>
        </div>
        <div class="resource-card__value">{{ myLeaves }}</div>
        <div class="resource-card__hint">用于兑换花种（落叶归根）</div>
      </div>
    </section>

    <!-- 行动条 -->
    <section class="action-bar card">
      <div class="action-bar__stats">
        <div class="action-bar__stat">
          <span class="action-bar__stat-num">{{ stats.total }}</span>
          <span class="action-bar__stat-label">总数</span>
        </div>
        <div class="action-bar__stat">
          <span class="action-bar__stat-num">{{ stats.bloomed }}</span>
          <span class="action-bar__stat-label">盛开</span>
        </div>
        <div class="action-bar__stat">
          <span class="action-bar__stat-num">{{ stats.wilted }}</span>
          <span class="action-bar__stat-label">待拾</span>
        </div>
      </div>
      <button class="btn btn--primary action-bar__cta" @click="goShop">
        🌿 去落叶画坊换花种
      </button>
    </section>

    <!-- 我的花朵列表 -->
    <section class="flowers-section">
      <div class="section-head">
        <h2 class="section-title">我的花朵</h2>
        <span class="section-count">{{ flowers.length }} 朵</span>
      </div>

      <div v-if="loading && !flowers.length" class="empty-state card">
        正在拾起散落的花种…
      </div>
      <div v-else-if="!flowers.length" class="empty-state card">
        <div class="empty-emoji">🌱</div>
        <p>花田还空着，去落叶画坊用落叶换一颗花种吧</p>
        <button class="btn btn--ghost" @click="goShop">前往落叶画坊 →</button>
      </div>

      <div v-else class="flower-groups">
        <div v-for="g in groupedFlowers" :key="g.type" class="flower-group">
          <div class="flower-group__title">
            <span class="flower-group__type">{{ g.type }}</span>
            <span class="flower-group__count">×{{ g.items.length }}</span>
          </div>
          <div class="flower-grid">
            <div
              v-for="f in g.items"
              :key="f.id"
              class="flower-card card"
              :class="{ 'flower-card--wilted': f.stage === 'wilted', 'flower-card--bloom': f.stage === 'bloom' }"
            >
              <div class="flower-card__emoji">{{ STAGE_INFO[f.stage]?.emoji || '🌱' }}</div>
              <div class="flower-card__body">
                <div class="flower-card__stage">{{ STAGE_INFO[f.stage]?.label || f.stage }}</div>
                <div class="flower-card__desc">{{ STAGE_INFO[f.stage]?.desc || '' }}</div>
                <!-- 生长进度条（枯萎不显示） -->
                <div class="flower-card__progress" v-if="f.stage !== 'wilted'">
                  <div class="flower-card__progress-bar" :style="{ width: STAGE_INFO[f.stage].progress + '%' }"></div>
                </div>
                <div class="flower-card__meta">
                  <span v-if="f.stage !== 'wilted' && f.stage !== 'bloom'">
                    浇水 {{ f.watered_count }}/{{ f.water_needed }}
                  </span>
                  <span v-else-if="f.stage === 'bloom'">
                    🌸 已盛开
                  </span>
                  <span v-else>可拾取落叶</span>
                  <span class="flower-card__date">· 种于 {{ formatDate(f.planted_at) }}</span>
                </div>
              </div>
              <div class="flower-card__actions">
                <button
                  v-if="f.stage !== 'wilted'"
                  class="btn btn--primary flower-card__btn"
                  :disabled="wateringId === f.id"
                  @click="waterFlower(f)"
                >
                  <span v-if="wateringId === f.id">💧…</span>
                  <span v-else>💧 浇水</span>
                </button>
                <button
                  v-else
                  class="btn btn--ghost flower-card__btn"
                  :disabled="collectingId === f.id"
                  @click="collectLeaves(f)"
                >
                  <span v-if="collectingId === f.id">🍂…</span>
                  <span v-else>🍂 拾叶</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 我的装扮/徽章 -->
    <section class="items-section" v-if="myItems.length">
      <div class="section-head">
        <h2 class="section-title">岛上物件</h2>
        <span class="section-count">{{ myItems.length }} 件</span>
      </div>
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

    <!-- 树洞相关说明 -->
    <section class="hint-section card">
      <div class="hint-section__emoji">🌸</div>
      <p class="hint-section__text">
        花朵需要用<strong>露水</strong>浇灌才能从种子 → 发芽 → 花苞 → 盛开。<br>
        盛开 7 天后未浇水会枯萎，枯萎后可拾取化作<strong>落叶</strong>，<br>
        落叶可在落叶画坊兑换新的花种 —— 寓意"落叶归根能施肥种花"。
      </p>
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

/* 平板紧凑 */
@media (min-width: 769px) and (max-width: 1024px) {
  .garden-view {
    padding: 28px 20px 72px;
  }
  .item-group__grid {
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 12px;
  }
}

/* 标题 */
.garden-header {
  text-align: center;
  margin-bottom: 24px;
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
  margin-bottom: 24px;
  border-radius: var(--radius-lg, 20px);
  overflow: hidden;
  box-shadow: var(--shadow-md, 0 4px 12px rgba(74, 68, 56, 0.08));
  /* 移动端兼容性：启用 GPU 合成 + 触摸滚动顺畅 */
  transform: translateZ(0);
  will-change: transform;
  -webkit-overflow-scrolling: touch;
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
  -webkit-backdrop-filter: blur(8px);
  border-radius: 16px;
  font-family: var(--font-serif, serif);
  font-size: 12px;
  color: var(--color-text-secondary, #5C4F3E);
  letter-spacing: 0.05em;
}

/* 双资源卡 */
.resource-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}
.resource-card {
  padding: 18px 20px;
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
  letter-spacing: 0.02em;
}

/* 行动条 */
.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 22px;
  margin-bottom: 28px;
  gap: 14px;
}
.action-bar__stats {
  display: flex;
  gap: 22px;
}
.action-bar__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.action-bar__stat-num {
  font-family: var(--font-serif, serif);
  font-size: 22px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  line-height: 1;
}
.action-bar__stat-label {
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.08em;
}
.action-bar__cta {
  white-space: nowrap;
}

/* 通用 section 标题 */
.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}
.section-title {
  font-family: var(--font-serif, serif);
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin: 0;
  letter-spacing: 0.05em;
}
.section-count {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  font-family: var(--font-serif, serif);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 36px 20px;
  color: var(--color-text-muted, #8B7B5E);
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.empty-emoji {
  font-size: 40px;
}

/* 花朵分组 */
.flowers-section {
  margin-bottom: 36px;
}
.flower-groups {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.flower-group__title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--color-text-secondary, #5C4F3E);
  margin-bottom: 10px;
  letter-spacing: 0.05em;
}
.flower-group__type {
  font-weight: 500;
}
.flower-group__count {
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
}
.flower-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

/* 花朵卡 */
.flower-card {
  padding: 16px 18px;
  display: flex;
  gap: 14px;
  align-items: flex-start;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 246, 240, 0.85) 100%);
  transition: transform 0.25s var(--ease-soft, ease), box-shadow 0.25s;
}
.flower-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.1));
}
.flower-card--bloom {
  background: linear-gradient(180deg, rgba(245, 168, 197, 0.18) 0%, rgba(255, 246, 240, 0.92) 100%);
}
.flower-card--wilted {
  background: linear-gradient(180deg, rgba(184, 165, 144, 0.18) 0%, rgba(255, 246, 240, 0.85) 100%);
}
.flower-card__emoji {
  font-size: 32px;
  line-height: 1;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.06));
}
.flower-card__body {
  flex: 1;
  min-width: 0;
}
.flower-card__stage {
  font-family: var(--font-serif, serif);
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 2px;
  letter-spacing: 0.05em;
}
.flower-card__desc {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  margin-bottom: 8px;
  line-height: 1.5;
}
.flower-card__progress {
  height: 6px;
  background: rgba(139, 123, 94, 0.12);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}
.flower-card__progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #A8C5A0 0%, #F5A8C5 100%);
  border-radius: 3px;
  transition: width 0.6s var(--ease-soft, ease);
}
.flower-card__meta {
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.flower-card__date {
  opacity: 0.7;
}
.flower-card__actions {
  flex-shrink: 0;
  align-self: center;
}
.flower-card__btn {
  min-width: 78px;
  padding: 8px 14px;
  font-size: 13px;
}

/* 装扮/徽章 */
.items-section {
  margin-bottom: 28px;
}
.items-groups {
  display: flex;
  flex-direction: column;
  gap: 20px;
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
.garden-item {
  padding: 14px 10px;
  text-align: center;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 246, 240, 0.85) 100%);
  transition: transform 0.25s var(--ease-soft, ease), box-shadow 0.25s;
}
.garden-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.1));
}
.garden-item__emoji {
  font-size: 30px;
  line-height: 1;
  margin-bottom: 6px;
}
.garden-item__name {
  font-family: var(--font-serif, serif);
  font-size: 12.5px;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 3px;
  letter-spacing: 0.03em;
}
.garden-item__date {
  font-size: 10.5px;
  color: var(--color-text-muted, #8B7B5E);
}

/* 提示区 */
.hint-section {
  padding: 22px 24px;
  text-align: center;
}
.hint-section__emoji {
  font-size: 24px;
  margin-bottom: 8px;
}
.hint-section__text {
  font-size: 13px;
  line-height: 1.9;
  color: var(--color-text-secondary, #5C4F3E);
  margin: 0;
}
.hint-section__text strong {
  color: var(--color-text-primary, #3D3327);
  font-weight: 500;
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

/* 响应式 */
@media (max-width: 768px) {
  .garden-view {
    padding: 20px 14px 80px;
  }
  .garden-header__title {
    font-size: 24px;
  }
  .garden-header__verse {
    font-size: 12px;
  }
  /* 3D 花田移动端降低高度 */
  .garden-hero {
    margin-bottom: 18px;
  }
  .garden-hero :deep(.flower-field) {
    height: 240px !important;
  }
  /* 移动端资源卡纵向更紧凑 */
  .resource-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 14px;
  }
  .resource-card {
    padding: 14px 14px;
  }
  .resource-card__value {
    font-size: 26px;
  }
  .resource-card__hint {
    font-size: 10.5px;
  }
  /* 行动条纵向 */
  .action-bar {
    flex-direction: column;
    padding: 16px 18px;
    gap: 14px;
  }
  .action-bar__stats {
    gap: 28px;
  }
  .action-bar__cta {
    width: 100%;
  }
  /* 花朵卡单列 */
  .flower-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .flower-card {
    padding: 14px 14px;
    gap: 12px;
  }
  .flower-card__emoji {
    font-size: 28px;
  }
  /* 装扮更紧凑 */
  .item-group__grid {
    grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
    gap: 10px;
  }
  .garden-item {
    padding: 10px 6px;
  }
  .garden-item__emoji {
    font-size: 24px;
  }
  .garden-item__name {
    font-size: 11.5px;
  }
  /* 提示区紧凑 */
  .hint-section {
    padding: 18px 16px;
  }
  .hint-section__text {
    font-size: 12px;
    line-height: 1.8;
  }
  /* toast 上移避开 tabbar */
  .toast {
    bottom: calc(90px + env(safe-area-inset-bottom));
  }
}
</style>
