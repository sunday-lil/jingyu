<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// v2.3：双资源系统（露水 + 落叶）
const myEnergy = computed(() => userStore.energy)
const myLeaves = computed(() => userStore.leaves)

// 货币展示信息
const CURRENCY_INFO = {
  dew:    { label: '露水', icon: '💧', accent: '#A8C5E8' },
  leaves: { label: '落叶', icon: '🍂', accent: '#D5A875' },
}

// 物品类型映射
const ITEM_TYPE_INFO = {
  flower:  { label: '花种', color: '#E8B8C5', desc: '用落叶兑换，种到屿上花田' },
  costume: { label: '装扮', color: '#A8B8C5', desc: '用露水兑换，点缀你的小岛' },
  badge:   { label: '徽章', color: '#E8C5A8', desc: '由静屿授予的纪念' },
}

// 当前激活的货币筛选（all / dew / leaves）
const activeCurrency = ref('all')

// 数据
const shopItems = ref([])
const loading = ref(false)
const exchangingId = ref(null) // 正在兑换的 item_id

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

// 按类型分组（同时按货币过滤）
const groupedShop = computed(() => {
  let items = shopItems.value
  // 按货币过滤
  if (activeCurrency.value !== 'all') {
    items = items.filter(i => (i.cost_currency || 'dew') === activeCurrency.value)
  }
  const groups = {}
  items.forEach(item => {
    const type = item.item_type || 'other'
    if (!groups[type]) groups[type] = []
    groups[type].push(item)
  })
  return Object.entries(groups).map(([type, list]) => ({
    type,
    label: ITEM_TYPE_INFO[type]?.label || type,
    color: ITEM_TYPE_INFO[type]?.color || '#B8A590',
    desc: ITEM_TYPE_INFO[type]?.desc || '',
    items: list.sort((a, b) => a.cost - b.cost),
  }))
})

// 是否能量不够
const isUnaffordable = (item) => {
  const currency = item.cost_currency || 'dew'
  const balance = currency === 'leaves' ? myLeaves.value : myEnergy.value
  return balance < (item.cost || 0)
}

// 拉取商店
const fetchShop = async () => {
  loading.value = true
  try {
    const shop = await api.get('/garden/shop')
    shopItems.value = shop || []
  } catch (e) {
    showToast(e.message || '商店加载失败', 2500)
  } finally {
    loading.value = false
  }
}

// 兑换物品（v2.3：花种用落叶，装扮用露水，徽章自动触发）
const exchange = async (item) => {
  if (exchangingId.value) return
  if (item.item_type === 'badge') {
    showToast('徽章由静屿自动授予，无需兑换 ✨', 2400)
    return
  }
  if (isUnaffordable(item)) {
    const currency = item.cost_currency || 'dew'
    const balance = currency === 'leaves' ? myLeaves.value : myEnergy.value
    const curInfo = CURRENCY_INFO[currency]
    showToast(`还差 ${item.cost - balance} ${curInfo.label} ${curInfo.icon}`, 2400)
    return
  }
  exchangingId.value = item.id
  try {
    const res = await api.post('/energy/exchange', { item_id: item.id })
    if (res?.success) {
      // 同步本地资源
      userStore.updateResources({
        total_energy: res.new_total_energy,
        leaves: res.new_leaves,
      })
      // 花种直接种到花田
      const gi = res.garden_item || {}
      if (gi.is_flower_seed) {
        showToast(`${item.image} 「${item.name}」已种到屿上花田 🌱`, 2800)
      } else {
        showToast(`${item.image} ${item.name} 已收入囊中 ✨`, 2800)
      }
    }
  } catch (e) {
    showToast(e.message || '兑换失败，请稍后再试', 2500)
  } finally {
    exchangingId.value = null
  }
}

const goGarden = () => router.push('/garden')

// 切换货币筛选
const setCurrency = (c) => {
  activeCurrency.value = c
  nextTick(() => {
    if (document.querySelector('.shop-card')) {
      gsap.from('.shop-card', {
        y: 12, opacity: 0, duration: 0.4, stagger: 0.04, ease: 'power2.out',
      })
    }
  })
}

onMounted(() => {
  fetchShop()
  nextTick(() => {
    gsap.from('.shop-header', { y: -20, opacity: 0, duration: 0.6, ease: 'power2.out' })
    gsap.from('.shop-energy', { y: 16, opacity: 0, duration: 0.55, ease: 'power3.out', delay: 0.1 })
    gsap.from('.currency-tabs', { y: 12, opacity: 0, duration: 0.5, ease: 'power2.out', delay: 0.15 })
    gsap.from('.shop-group', {
      y: 24, opacity: 0, duration: 0.55, stagger: 0.12, ease: 'power2.out', delay: 0.2,
    })
    gsap.from('.shop-card', {
      y: 18, opacity: 0, duration: 0.45, stagger: 0.05, ease: 'power2.out', delay: 0.35,
    })
  })
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="shop-view">
    <!-- 顶部标题 -->
    <header class="shop-header">
      <h1 class="shop-header__title">花坊</h1>
      <p class="shop-header__verse">"落叶归根能施肥种花，露水浇花使其盛开"</p>
    </header>

    <!-- 双资源条 -->
    <section class="shop-energy card">
      <div class="shop-energy__left">
        <div class="shop-energy__item">
          <span class="shop-energy__icon">💧</span>
          <div>
            <div class="shop-energy__label">露水</div>
            <div class="shop-energy__num">{{ myEnergy }}</div>
          </div>
        </div>
        <div class="shop-energy__divider"></div>
        <div class="shop-energy__item">
          <span class="shop-energy__icon">🍂</span>
          <div>
            <div class="shop-energy__label">落叶</div>
            <div class="shop-energy__num">{{ myLeaves }}</div>
          </div>
        </div>
      </div>
      <button class="btn btn--ghost shop-energy__cta" @click="goGarden">
        ← 回花田
      </button>
    </section>

    <!-- 货币筛选 Tab -->
    <section class="currency-tabs">
      <button
        class="currency-tab"
        :class="{ 'is-active': activeCurrency === 'all' }"
        @click="setCurrency('all')"
      >全部</button>
      <button
        class="currency-tab"
        :class="{ 'is-active': activeCurrency === 'leaves' }"
        @click="setCurrency('leaves')"
      >
        🍂 落叶花种
      </button>
      <button
        class="currency-tab"
        :class="{ 'is-active': activeCurrency === 'dew' }"
        @click="setCurrency('dew')"
      >
        💧 露水装扮
      </button>
    </section>

    <!-- 加载中 -->
    <div v-if="loading && !shopItems.length" class="shop-empty">正在打开画坊的门…</div>
    <div v-else-if="!shopItems.length" class="shop-empty">画坊还没有上架物品</div>
    <div v-else-if="!groupedShop.length" class="shop-empty">此分类下暂无物品</div>

    <!-- 物品分组 -->
    <section
      v-for="g in groupedShop"
      :key="g.type"
      class="shop-group"
    >
      <div class="shop-group__head">
        <span class="shop-group__dot" :style="{ background: g.color }"></span>
        <div>
          <div class="shop-group__title">{{ g.label }}</div>
          <div class="shop-group__desc">{{ g.desc }}</div>
        </div>
      </div>
      <div class="shop-group__grid">
        <div
          v-for="item in g.items"
          :key="item.id"
          class="shop-card card"
          :class="{
            'is-unaffordable': item.item_type !== 'badge' && isUnaffordable(item),
            'is-badge': item.item_type === 'badge',
          }"
        >
          <div class="shop-card__emoji">{{ item.image }}</div>
          <div class="shop-card__name">{{ item.name }}</div>
          <div class="shop-card__desc" v-if="item.description">{{ item.description }}</div>
          <div class="shop-card__foot">
            <div class="shop-card__cost">
              <span class="shop-card__cost-icon">{{ CURRENCY_INFO[item.cost_currency || 'dew'].icon }}</span>
              <span class="shop-card__cost-num">{{ item.cost }}</span>
            </div>
            <button
              v-if="item.item_type === 'badge'"
              class="btn btn--ghost shop-card__btn"
              disabled
              title="徽章由静屿自动授予"
            >
              待授予
            </button>
            <button
              v-else
              class="btn btn--primary shop-card__btn"
              :disabled="exchangingId === item.id || isUnaffordable(item)"
              @click="exchange(item)"
            >
              <span v-if="exchangingId === item.id">兑换中…</span>
              <span v-else-if="isUnaffordable(item)">{{ CURRENCY_INFO[item.cost_currency || 'dew'].label }}不足</span>
              <span v-else>兑换</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 说明区 -->
    <section class="shop-hint card">
      <div class="shop-hint__emoji">🌿</div>
      <p class="shop-hint__text">
        <strong>花种</strong>用落叶兑换，兑换后直接种到屿上花田（种子阶段）；<br>
        <strong>装扮</strong>用露水兑换，会出现在你的岛上物件里；<br>
        <strong>徽章</strong>由静屿在你达成条件时自动授予，无需兑换。
      </p>
    </section>

    <!-- toast -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.shop-view {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* 平板紧凑 */
@media (min-width: 769px) and (max-width: 1024px) {
  .shop-view {
    padding: 28px 20px 72px;
  }
  .shop-group__grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 14px;
  }
}

/* 标题 */
.shop-header {
  text-align: center;
  margin-bottom: 24px;
}
.shop-header__title {
  font-family: var(--font-serif, serif);
  font-size: 30px;
  font-weight: 500;
  letter-spacing: 0.1em;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
}
.shop-header__verse {
  font-family: var(--font-serif, serif);
  font-style: italic;
  font-size: 14px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
  letter-spacing: 0.05em;
}

/* 双资源条 */
.shop-energy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  margin-bottom: 18px;
  background: linear-gradient(135deg, rgba(168, 197, 232, 0.18) 0%, rgba(213, 168, 117, 0.18) 100%);
  gap: 14px;
}
.shop-energy__left {
  display: flex;
  align-items: center;
  gap: 18px;
  flex: 1;
  min-width: 0;
}
.shop-energy__item {
  display: flex;
  align-items: center;
  gap: 10px;
}
.shop-energy__icon {
  font-size: 28px;
}
.shop-energy__label {
  font-family: var(--font-serif, serif);
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.06em;
  margin-bottom: 2px;
}
.shop-energy__num {
  font-family: var(--font-serif, serif);
  font-size: 24px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  letter-spacing: 0.02em;
  line-height: 1;
}
.shop-energy__divider {
  width: 1px;
  height: 32px;
  background: rgba(139, 123, 94, 0.18);
}
.shop-energy__cta {
  white-space: nowrap;
  flex-shrink: 0;
}

/* 货币筛选 Tab */
.currency-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}
.currency-tab {
  padding: 8px 18px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.5);
  color: var(--color-text-secondary, #5C4F3E);
  font-size: 13px;
  font-family: var(--font-serif, serif);
  letter-spacing: 0.05em;
  border: 1px solid rgba(184, 165, 144, 0.2);
  cursor: pointer;
  transition: all 0.25s var(--ease-soft, ease);
}
.currency-tab:hover {
  background: rgba(255, 255, 255, 0.8);
}
.currency-tab.is-active {
  background: linear-gradient(135deg, rgba(184, 165, 144, 0.25), rgba(255, 255, 255, 0.6));
  color: var(--color-text-primary, #3D3327);
  border-color: rgba(184, 165, 144, 0.4);
}

/* 空状态 */
.shop-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-muted, #8B7B5E);
  font-size: 14px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-lg, 20px);
}

/* 分组 */
.shop-group {
  margin-bottom: 36px;
}
.shop-group__head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.shop-group__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}
.shop-group__title {
  font-family: var(--font-serif, serif);
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  letter-spacing: 0.05em;
}
.shop-group__desc {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  margin-top: 2px;
}
.shop-group__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

/* 卡片 */
.shop-card {
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(255, 246, 240, 0.92) 100%);
  transition: transform 0.25s var(--ease-soft, ease), box-shadow 0.25s;
}
.shop-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.12));
}
.shop-card.is-unaffordable {
  opacity: 0.7;
}
.shop-card.is-badge {
  background: linear-gradient(180deg, rgba(232, 197, 168, 0.22) 0%, rgba(255, 246, 240, 0.92) 100%);
}
.shop-card__emoji {
  font-size: 44px;
  line-height: 1;
  margin-bottom: 10px;
  filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.08));
}
.shop-card__name {
  font-family: var(--font-serif, serif);
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 6px;
  letter-spacing: 0.03em;
}
.shop-card__desc {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  line-height: 1.5;
  margin-bottom: 12px;
  min-height: 32px;
}
.shop-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin-top: auto;
  padding-top: 8px;
}
.shop-card__cost {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: var(--font-serif, serif);
}
.shop-card__cost-icon {
  font-size: 16px;
}
.shop-card__cost-num {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
}
.shop-card__btn {
  min-width: 76px;
  padding: 6px 14px;
  font-size: 13px;
}

/* 说明区 */
.shop-hint {
  padding: 22px 24px;
  text-align: center;
  margin-top: 8px;
}
.shop-hint__emoji {
  font-size: 24px;
  margin-bottom: 8px;
}
.shop-hint__text {
  font-size: 13px;
  line-height: 1.9;
  color: var(--color-text-secondary, #5C4F3E);
  margin: 0;
}
.shop-hint__text strong {
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
  .shop-view {
    padding: 20px 14px 80px;
  }
  .shop-header__title {
    font-size: 24px;
  }
  .shop-header__verse {
    font-size: 12px;
  }
  /* 双资源条纵向 */
  .shop-energy {
    flex-direction: column;
    gap: 14px;
    padding: 16px 18px;
    text-align: center;
  }
  .shop-energy__left {
    width: 100%;
    justify-content: space-around;
    gap: 8px;
  }
  .shop-energy__item {
    flex-direction: column;
    gap: 4px;
  }
  .shop-energy__cta {
    width: 100%;
  }
  /* 货币筛选 tab：横向滚动 */
  .currency-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    flex-wrap: nowrap;
    margin-bottom: 22px;
    padding-bottom: 4px;
  }
  .currency-tab {
    flex-shrink: 0;
    padding: 7px 14px;
    font-size: 12px;
  }
  /* 商店卡片 2 列 */
  .shop-group__grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .shop-card {
    padding: 14px 10px;
  }
  .shop-card__emoji {
    font-size: 34px;
  }
  .shop-card__name {
    font-size: 13.5px;
  }
  .shop-card__desc {
    font-size: 11px;
    min-height: 28px;
    -webkit-line-clamp: 2;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .shop-card__btn {
    min-width: 64px;
    padding: 6px 10px;
    font-size: 12px;
  }
  .shop-card__cost-num {
    font-size: 14px;
  }
  .shop-hint {
    padding: 18px 16px;
  }
  .shop-hint__text {
    font-size: 12px;
    line-height: 1.8;
  }
  /* toast 上移避开 tabbar */
  .toast {
    bottom: calc(90px + env(safe-area-inset-bottom));
  }
}
</style>
