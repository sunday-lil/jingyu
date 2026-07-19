<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 物品类型映射
const ITEM_TYPE_INFO = {
  plant: { label: '植物', color: '#A8C5A0', desc: '在角落里静静生长' },
  flower: { label: '花卉', color: '#E8B8C5', desc: '为花园添一抹颜色' },
  stone: { label: '石头', color: '#B8A590', desc: '稳稳地落在土地上' },
  ornament: { label: '装饰', color: '#A8B8C5', desc: '让花园更有故事' },
  badge: { label: '徽章', color: '#E8C5A8', desc: '由静屿授予的纪念' },
}

// 数据
const shopItems = ref([])
const myItemIds = ref(new Set()) // 我已持有的 item_id 集合
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

// 我的能量
const myEnergy = computed(() => userStore.energy)

// 按类型分组
const groupedShop = computed(() => {
  const groups = {}
  shopItems.value.forEach(item => {
    const type = item.item_type || 'other'
    if (!groups[type]) groups[type] = []
    groups[type].push(item)
  })
  return Object.entries(groups).map(([type, items]) => ({
    type,
    label: ITEM_TYPE_INFO[type]?.label || type,
    color: ITEM_TYPE_INFO[type]?.color || '#B8A590',
    desc: ITEM_TYPE_INFO[type]?.desc || '',
    items: items.sort((a, b) => a.cost - b.cost),
  }))
})

// 是否已持有
const isOwned = (itemId) => myItemIds.value.has(itemId)

// 是否能量不够
const isUnaffordable = (cost) => myEnergy.value < cost

// 拉取商店 + 我的持有
const fetchAll = async () => {
  loading.value = true
  try {
    const [shop, mine] = await Promise.all([
      api.get('/garden/shop'),
      api.get('/garden/mine'),
    ])
    shopItems.value = shop || []
    myItemIds.value = new Set((mine?.items || []).map(i => i.item_id))
  } catch (e) {
    showToast(e.message || '商店加载失败', 2500)
  } finally {
    loading.value = false
  }
}

// 兑换物品
const exchange = async (item) => {
  if (exchangingId.value) return
  if (isOwned(item.id)) {
    showToast('已经拥有这件物品了 ✨', 2200)
    return
  }
  if (isUnaffordable(item.cost)) {
    showToast(`还差 ${item.cost - myEnergy.value} 滴露水 🌿`, 2200)
    return
  }
  exchangingId.value = item.id
  try {
    const res = await api.post('/energy/exchange', { item_id: item.id })
    if (res?.success) {
      // 更新本地能量
      userStore.updateEnergy(res.new_total_energy)
      // 标记为已持有
      myItemIds.value = new Set([...myItemIds.value, item.id])
      showToast(`${item.image} ${item.name} 已种进你的花园`, 2800)
    }
  } catch (e) {
    showToast(e.message || '兑换失败，请稍后再试', 2500)
  } finally {
    exchangingId.value = null
  }
}

const goGarden = () => router.push('/garden')

onMounted(() => {
  fetchAll()
  nextTick(() => {
    gsap.from('.shop-header', { y: -20, opacity: 0, duration: 0.6, ease: 'power2.out' })
    gsap.from('.shop-energy', { y: 16, opacity: 0, duration: 0.55, ease: 'power3.out', delay: 0.1 })
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
      <h1 class="shop-header__title">露水商店</h1>
      <p class="shop-header__verse">"用收集到的露水，换一些不会凋谢的小小生命"</p>
    </header>

    <!-- 能量条 -->
    <section class="shop-energy card">
      <div class="shop-energy__left">
        <span class="shop-energy__icon">💧</span>
        <div>
          <div class="shop-energy__label">我的露水</div>
          <div class="shop-energy__num">{{ myEnergy }}</div>
        </div>
      </div>
      <button class="btn btn--ghost shop-energy__cta" @click="goGarden">
        ← 回到花园
      </button>
    </section>

    <!-- 加载中 -->
    <div v-if="loading && !shopItems.length" class="shop-empty">正在打开商店的门…</div>
    <div v-else-if="!shopItems.length" class="shop-empty">商店还没有上架物品</div>

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
            'is-owned': isOwned(item.id),
            'is-unaffordable': !isOwned(item.id) && isUnaffordable(item.cost),
          }"
        >
          <div class="shop-card__emoji">{{ item.image }}</div>
          <div class="shop-card__name">{{ item.name }}</div>
          <div class="shop-card__desc" v-if="item.description">{{ item.description }}</div>
          <div class="shop-card__foot">
            <div class="shop-card__cost">
              <span class="shop-card__cost-icon">💧</span>
              <span class="shop-card__cost-num">{{ item.cost }}</span>
            </div>
            <button
              v-if="isOwned(item.id)"
              class="btn btn--ghost shop-card__btn"
              disabled
            >
              已拥有
            </button>
            <button
              v-else
              class="btn btn--primary shop-card__btn"
              :disabled="exchangingId === item.id || isUnaffordable(item.cost)"
              @click="exchange(item)"
            >
              <span v-if="exchangingId === item.id">兑换中…</span>
              <span v-else-if="isUnaffordable(item.cost)">露水不足</span>
              <span v-else>兑换</span>
            </button>
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
.shop-view {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* 标题 */
.shop-header {
  text-align: center;
  margin-bottom: 28px;
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

/* 能量条 */
.shop-energy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  margin-bottom: 36px;
  background: linear-gradient(135deg, rgba(168, 197, 232, 0.18) 0%, rgba(232, 184, 197, 0.18) 100%);
}
.shop-energy__left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.shop-energy__icon {
  font-size: 32px;
}
.shop-energy__label {
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.06em;
  margin-bottom: 2px;
}
.shop-energy__num {
  font-family: var(--font-serif, serif);
  font-size: 28px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  letter-spacing: 0.02em;
}
.shop-energy__cta {
  min-width: 130px;
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
  margin-bottom: 40px;
}
.shop-group__head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
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
.shop-card.is-owned {
  background: linear-gradient(180deg, rgba(168, 197, 160, 0.18) 0%, rgba(255, 246, 240, 0.85) 100%);
}
.shop-card.is-unaffordable {
  opacity: 0.7;
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
  .shop-view {
    padding: 20px 14px 60px;
  }
  .shop-header__title {
    font-size: 24px;
  }
  .shop-energy {
    flex-direction: column;
    gap: 14px;
    padding: 18px 16px;
    text-align: center;
  }
  .shop-energy__left {
    flex-direction: column;
    gap: 6px;
  }
  .shop-energy__cta {
    width: 100%;
  }
  .shop-group__grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }
  .shop-card {
    padding: 16px 12px;
  }
  .shop-card__emoji {
    font-size: 36px;
  }
  .shop-card__name {
    font-size: 14px;
  }
}
</style>
