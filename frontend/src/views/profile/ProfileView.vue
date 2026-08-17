<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'
import { useUserStore } from '@/stores/user'
import EmojiIcon from '@/components/EmojiIcon.vue'

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

// 当前头像（优先 profile 数据，兜底 store）
const currentAvatar = computed(() => profile.value?.avatar || userStore.avatar || '🙂')

// 头像是否是图片 URL（vs emoji 文本）
const isAvatarImage = computed(() => {
  const a = currentAvatar.value
  return !!(a && (a.startsWith('/') || a.startsWith('http')))
})
const isEditAvatarImage = computed(() => {
  const a = editAvatar.value
  return !!(a && (a.startsWith('/') || a.startsWith('http')))
})

// 上传头像图片（拍摄 / 相册）
const onAvatarUpload = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    showToast('图片不能超过 2MB')
    e.target.value = ''
    return
  }
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await api.post('/profile/avatar', formData)
    if (res?.avatar) {
      editAvatar.value = res.avatar
      showToast('图片已上传，点保存生效')
    }
  } catch (err) {
    showToast(err.message || '上传失败')
  }
  e.target.value = ''
}

// ─── 编辑头像 / 昵称 ───
const editModalVisible = ref(false)
const editNickname = ref('')
const editAvatar = ref('')
const editSaving = ref(false)

// 可选头像 emoji 列表
const AVATAR_CHOICES = [
  '🙂', '😊', '😌', '🥰', '😎', '🤗', '😇', '🤔',
  '😴', '🥺', '😏', '🌴', '🌸', '🍀', '🌙', '⭐',
  '🐳', '🦊', '🐱', '🦌', '🐢', '🦋', '🌿', '🍄',
]

const openEditModal = () => {
  editNickname.value = profile.value?.nickname || userStore.nickname || ''
  editAvatar.value = currentAvatar.value
  editModalVisible.value = true
}

const closeEditModal = () => {
  editModalVisible.value = false
}

const saveProfile = async () => {
  const nick = editNickname.value.trim()
  if (nick.length < 2) {
    showToast('昵称至少 2 个字')
    return
  }
  if (!editAvatar.value) {
    showToast('选一个头像吧')
    return
  }
  editSaving.value = true
  try {
    const payload = { nickname: nick }
    // 头像是图片 URL 时已由上传端点更新数据库，PATCH 只接受 emoji（≤16字符），不重复发送
    if (!isEditAvatarImage.value) {
      payload.avatar = editAvatar.value
    }
    const updated = await userStore.updateProfile(payload)
    profile.value = { ...profile.value, ...updated }
    showToast('已更新 ✨')
    editModalVisible.value = false
  } catch (e) {
    showToast(e.message || '更新失败，稍后再试')
  } finally {
    editSaving.value = false
  }
}

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
    // 同步本地 store 的资源 + 头像
    if (typeof p?.total_energy === 'number') {
      userStore.updateResources({
        total_energy: p.total_energy,
        leaves: p.leaves,
      })
    }
    if (p?.avatar && userStore.user) {
      userStore.user.avatar = p.avatar
      localStorage.setItem('qi_user', JSON.stringify(userStore.user))
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
  // 只做位移动画，不设 opacity 初始态（防动画中断后永久不可见）
  gsap.from('.profile-hero', { y: -20, duration: 0.6, ease: 'power2.out' })
  gsap.from('.stat-card', {
    y: 18, duration: 0.5, stagger: 0.06, ease: 'power3.out', delay: 0.1,
  })
  if (document.querySelector('.badge-card')) {
    gsap.from('.badge-card', {
      y: 14, duration: 0.45, stagger: 0.06, ease: 'power2.out', delay: 0.3,
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

// ─── 静屿使用指南 ───
const guideOpen = ref(null)
const GUIDE_SECTIONS = [
  {
    icon: '🎵', title: '琴音疗心',
    desc: '宫商角徵羽五音古曲 + 古琴弹西洋曲谱两个子板块。',
    details: [
      '五音古曲：按宫（土/脾胃）、商（金/肺）、角（木/肝）、徵（火/心）、羽（水/肾）分类，每种音对应不同的调理方向。',
      '古琴弹西洋：用古琴演绎绿袖子、卡农等西洋旋律，中西合璧。',
      '每听完一首曲子可获得 1 露水（每日上限 20），听满 10 首自动获得「琴音知音」徽章。',
      '不确定听哪首时，可在页面内让 AI 根据你当下的状态推荐一个音。',
    ],
  },
  {
    icon: '📖', title: '日记海岸（漂流日记）',
    desc: '把心事写进瓶子，让它漂向远方。',
    details: [
      '写日记：可选择「放入漂流瓶」（公开可见，可被陌生人拾取并留鼓励）或「不放入漂流瓶」（仅自己可见，同步至树洞）。',
      '拾瓶：随机拾取一条陌生人公开的漂流瓶，阅读后可留一句匿名鼓励。',
      '每写一篇日记 +2 露水（每日上限 10），每留一句鼓励 +1 露水（每日上限 10）。',
      '写满 30 篇日记自动获得「日记达人」徽章，拾满 10 个瓶子获得「拾瓶旅人」徽章。',
    ],
  },
  {
    icon: '🌙', title: '情绪日历',
    desc: '记录每天的心情轨迹，画进日历里。',
    details: [
      '今日打卡：选择一个或多个此刻的心情（支持一天多次打卡，情绪是多变的）。',
      '日历网格：每天显示当日记录的心情 emoji，点击可回看。',
      '情绪环状图：基于「罗素情绪环模型」，横轴为效价（消极→积极），纵轴为唤醒度（平静→激烈），把记录的情绪定位到四象限里，直观看到情绪分布。',
      '连续打卡 7 天自动获得「七日静心」徽章（赠 7 落叶）。',
    ],
  },
  {
    icon: '🌳', title: '心语树洞',
    desc: '说给一棵树听，它不会告诉任何人。',
    details: [
      '与 AI 树洞多轮对话，像一个会回话的朋友，倾听、不评判。',
      '如果当天在情绪日历打过卡、或写过不公开的日记，树洞会温柔地接住这些上下文。',
      '对话满 20 次自动获得「树洞倾心」徽章。',
      '树洞里显示的头像与「我的」页面头像一致，可在个人主页修改。',
    ],
  },
  {
    icon: '🍂', title: '落叶花坊',
    desc: '落叶归根，化作春泥换花种。',
    details: [
      '用落叶兑换花种（向日葵、竹子、樱花、薰衣草、郁金香等 11 种植物，介绍均为花语）。',
      '落叶来源：花田里枯萎的花朵拾取后转化得到；解锁徽章也会赠落叶（按难度 7~20 片不等）。',
      '用露水兑换装扮（竹编帽、油纸伞、斗篷、乌篷船、鱼竿、橘猫、小鸟、小鸭、小狗、火烈鸟等）。',
      '装扮和徽章会显示在「屿上花田」和「我的」页面。',
    ],
  },
  {
    icon: '🌸', title: '屿上花田',
    desc: '在静屿的土壤里，种下属于你的花。',
    details: [
      '花种从落叶花坊兑换后自动种入花田，经历种子 → 发芽 → 花苞 → 盛开 → 枯萎的完整周期。',
      '浇水消耗 1 露水，每朵花需要浇一定次数才能进入下一阶段。',
      '盛开后不再需要浇水，7 天后未浇水会枯萎。',
      '枯萎后可拾取化作落叶（落叶又能在落叶花坊换新花种 —— 落叶归根循环）。',
      '种满 10 朵花自动获得「花间客」徽章（解锁即赠 10 落叶）。',
    ],
  },
  {
    icon: '👤', title: '我的',
    desc: '岛上足迹、资源、物件一览。',
    details: [
      '岛上足迹：日记数、打卡天数、听曲数、花朵数、收到鼓励数、岛上物件数，点击可跳转对应板块。',
      '前往各处：六个板块的快捷入口。',
      '可点击头像旁的「编辑」按钮修改头像和昵称，头像会同步到树洞。',
    ],
  },
]

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
      <div class="profile-hero__avatar" @click="openEditModal" title="点击修改头像和昵称">
        <img v-if="isAvatarImage" :src="currentAvatar" class="avatar-img" alt="头像" />
        <EmojiIcon v-else :emoji="currentAvatar" />
        <span class="profile-hero__avatar-edit">✎</span>
      </div>
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
        <button class="btn btn--ghost profile-hero__btn" @click="openEditModal"><EmojiIcon emoji="✎" /> 编辑</button>
        <button class="btn btn--ghost profile-hero__btn" @click="goNotifications"><EmojiIcon emoji="🔔" /> 通知</button>
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
            <div class="resource-card__icon"><EmojiIcon emoji="💧" /></div>
          </div>
          <div class="resource-card__value">{{ profile.total_energy }}</div>
          <div class="resource-card__hint">浇灌花朵盛开</div>
        </div>
        <div class="resource-card card">
          <div class="resource-card__head">
            <div class="resource-card__label">落叶</div>
            <div class="resource-card__icon"><EmojiIcon emoji="🍂" /></div>
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
                  <div class="stat-card__emoji"><EmojiIcon emoji="📖" /></div>
                  <div class="stat-card__num">{{ profile.stats.diary_count }}</div>
                  <div class="stat-card__label">日记</div>
                  <div class="stat-card__sub" v-if="profile.stats.public_diary_count">
                    公开 {{ profile.stats.public_diary_count }}
                  </div>
                </button>
                <button class="stat-card card" @click="goCalendar">
                  <div class="stat-card__emoji"><EmojiIcon emoji="🌙" /></div>
                  <div class="stat-card__num">{{ profile.stats.checkin_count }}</div>
                  <div class="stat-card__label">打卡</div>
                  <div class="stat-card__sub">连续 {{ profile.stats.streak }} 天</div>
                </button>
                <button class="stat-card card" @click="goMusic">
                  <div class="stat-card__emoji"><EmojiIcon emoji="🎵" /></div>
                  <div class="stat-card__num">{{ profile.stats.listen_count }}</div>
                  <div class="stat-card__label">听曲</div>
                  <div class="stat-card__sub">古琴疗愈</div>
                </button>
                <button class="stat-card card" @click="goGarden">
                  <div class="stat-card__emoji"><EmojiIcon emoji="🌸" /></div>
                  <div class="stat-card__num">{{ flowerStats.total }}</div>
                  <div class="stat-card__label">花朵</div>
                  <div class="stat-card__sub">盛开 {{ flowerStats.bloom }}</div>
                </button>
                <div class="stat-card card" @click="goNotifications">
                  <div class="stat-card__emoji"><EmojiIcon emoji="💛" /></div>
                  <div class="stat-card__num">{{ profile.stats.received_encouragement_count }}</div>
                  <div class="stat-card__label">收到鼓励</div>
                  <div class="stat-card__sub">来自漂流瓶</div>
                </div>
                <div class="stat-card card" @click="goGarden">
                  <div class="stat-card__emoji"><EmojiIcon emoji="🧳" /></div>
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
            <span class="quick-card__emoji"><EmojiIcon emoji="🌸" /></span>
            <span class="quick-card__label">屿上花田</span>
          </button>
          <button class="quick-card card" @click="goShop">
            <span class="quick-card__emoji"><EmojiIcon emoji="🍂" /></span>
            <span class="quick-card__label">落叶花坊</span>
          </button>
          <button class="quick-card card" @click="goDiary">
            <span class="quick-card__emoji"><EmojiIcon emoji="📖" /></span>
            <span class="quick-card__label">日记海岸</span>
          </button>
          <button class="quick-card card" @click="goCalendar">
            <span class="quick-card__emoji"><EmojiIcon emoji="🌙" /></span>
            <span class="quick-card__label">情绪日历</span>
          </button>
          <button class="quick-card card" @click="goMusic">
            <span class="quick-card__emoji"><EmojiIcon emoji="🎵" /></span>
            <span class="quick-card__label">琴音疗心</span>
          </button>
          <button class="quick-card card" @click="goAiChat">
            <span class="quick-card__emoji"><EmojiIcon emoji="🌳" /></span>
            <span class="quick-card__label">心语树洞</span>
          </button>
        </div>
      </section>

      <!-- 静屿使用指南 -->
      <section class="guide-section">
        <h2 class="section-title">静屿使用指南</h2>
        <p class="guide-section__subtitle">六个去处 · 每一处都有它的用意</p>
        <div class="guide-list">
          <div
            v-for="(s, i) in GUIDE_SECTIONS"
            :key="i"
            class="guide-card card"
          >
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
            <div class="flower-mini__emoji"><EmojiIcon :emoji="STAGE_INFO[f.stage]?.emoji || '🌱'" /></div>
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
        <div class="empty-island__emoji"><EmojiIcon emoji="🏝️" /></div>
        <p class="empty-island__text">
          你的小岛还很安静，<br>
          去写一篇日记、听一曲古琴，或种下一朵花吧。
        </p>
        <button class="btn btn--primary" @click="goDiary">写一篇日记</button>
      </section>
    </template>

    <!-- 编辑头像 / 昵称弹窗 -->
    <transition name="modal">
      <div v-if="editModalVisible" class="modal-mask" @click.self="closeEditModal">
        <div class="modal-card card">
          <div class="modal-card__head">
            <h3 class="modal-card__title">修改头像和昵称</h3>
            <button class="modal-card__close" @click="closeEditModal" aria-label="关闭">×</button>
          </div>
          <div class="modal-card__body">
            <!-- 头像选择 -->
            <div class="edit-field">
              <label class="edit-field__label">头像（与树洞一致）</label>
              <div class="avatar-preview">
                <img v-if="isEditAvatarImage" :src="editAvatar" class="avatar-preview-img" alt="" />
                <span v-else>{{ editAvatar }}</span>
              </div>
              <div class="avatar-upload">
                <label class="avatar-upload__btn">
                  📷 拍照 / 从相册选择
                  <input type="file" accept="image/*" @change="onAvatarUpload" hidden />
                </label>
              </div>
              <div class="avatar-grid">
                <button
                  v-for="a in AVATAR_CHOICES"
                  :key="a"
                  class="avatar-grid__btn"
                  :class="{ 'is-selected': editAvatar === a }"
                  @click="editAvatar = a"
                >{{ a }}</button>
              </div>
            </div>
            <!-- 昵称输入 -->
            <div class="edit-field">
              <label class="edit-field__label">昵称（2-20 字）</label>
              <input
                v-model="editNickname"
                class="edit-field__input"
                type="text"
                maxlength="20"
                placeholder="给自己起个名字"
              />
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn btn--ghost" @click="closeEditModal">取消</button>
            <button class="btn btn--primary" :disabled="editSaving" @click="saveProfile">
              {{ editSaving ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

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
  cursor: pointer;
  position: relative;
  transition: transform 0.25s var(--ease-soft, ease);
}
.profile-hero__avatar:hover {
  transform: scale(1.05);
}
.profile-hero__avatar-edit {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--color-accent, #B8A590);
  color: #fff;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  opacity: 0;
  transition: opacity 0.25s;
}
.profile-hero__avatar:hover .profile-hero__avatar-edit {
  opacity: 1;
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

/* 使用指南 */
.guide-section {
  margin-bottom: 32px;
}
.guide-section__subtitle {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0 0 18px;
  letter-spacing: 0.05em;
}
.guide-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 2px;
  letter-spacing: 0.05em;
}
.guide-card__desc {
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  line-height: 1.5;
}
.guide-card__arrow {
  font-size: 20px;
  color: var(--color-text-muted, #8B7B5E);
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
  color: var(--color-text-secondary, #5C4F3E);
  margin: 0 0 4px;
  position: relative;
  padding-left: 14px;
}
.guide-card__detail::before {
  content: '·';
  position: absolute;
  left: 0;
  color: var(--color-text-muted, #8B7B5E);
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

/* 编辑弹窗 */
.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: rgba(61, 51, 39, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-card {
  width: 100%;
  max-width: 420px;
  max-height: 85vh;
  overflow-y: auto;
  padding: 24px;
}
.modal-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.modal-card__title {
  font-family: var(--font-serif, serif);
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin: 0;
  letter-spacing: 0.05em;
}
.modal-card__close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
  border: none;
  font-size: 22px;
  line-height: 1;
  color: var(--color-text-muted, #8B7B5E);
  cursor: pointer;
  display: grid;
  place-items: center;
}
.modal-card__body {
  margin-bottom: 20px;
}
.edit-field {
  margin-bottom: 18px;
}
.edit-field__label {
  display: block;
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-secondary, #5C4F3E);
  margin-bottom: 10px;
  letter-spacing: 0.05em;
}
.avatar-preview {
  text-align: center;
  font-size: 48px;
  margin-bottom: 14px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-preview-img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
}
.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
.avatar-upload {
  text-align: center;
  margin-bottom: 14px;
}
.avatar-upload__btn {
  display: inline-block;
  padding: 8px 18px;
  border-radius: var(--radius-md, 14px);
  background: rgba(184, 165, 144, 0.12);
  color: var(--color-text-secondary, #5C4F3E);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  font-family: inherit;
}
.avatar-upload__btn:hover {
  background: rgba(184, 165, 144, 0.22);
}
.avatar-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 6px;
}
.avatar-grid__btn {
  aspect-ratio: 1;
  border-radius: var(--radius-md, 14px);
  background: rgba(255, 255, 255, 0.5);
  border: 2px solid transparent;
  font-size: 22px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s var(--ease-soft, ease);
}
.avatar-grid__btn:hover {
  background: rgba(255, 255, 255, 0.85);
  transform: scale(1.1);
}
.avatar-grid__btn.is-selected {
  border-color: var(--color-accent, #B8A590);
  background: rgba(184, 165, 144, 0.15);
}
.edit-field__input {
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--radius-md, 14px);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  background: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  color: var(--color-text-primary, #3D3327);
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}
.edit-field__input:focus {
  border-color: var(--color-accent, #B8A590);
}
.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s var(--ease-soft, ease);
}
.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition: transform 0.3s var(--ease-soft, ease);
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-card,
.modal-leave-to .modal-card {
  transform: scale(0.95) translateY(10px);
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
  /* 物件 / 指南 */
  .avatar-grid {
    grid-template-columns: repeat(6, 1fr);
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
