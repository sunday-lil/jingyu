<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import gsap from 'gsap'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 心情常量（与后端 app/utils/constants.py:MOOD_INFO 完全对齐 —— v2.3 七种心情）
// score 用于趋势条高度计算（1~5）
const MOOD_INFO = {
  ecstatic: { emoji: '🤩', label: '极度开心', score: 5, color: '#FFD56B' },
  happy:    { emoji: '😊', label: '开心',     score: 4, color: '#F6B26B' },
  calm:     { emoji: '😌', label: '平静',     score: 3, color: '#A8D5BA' },
  tired:    { emoji: '😪', label: '疲惫',     score: 2, color: '#B8B5C5' },
  anxious:  { emoji: '😰', label: '焦虑',     score: 2, color: '#9BB5D5' },
  angry:    { emoji: '😠', label: '生气',     score: 1, color: '#E89A9A' },
  sad:      { emoji: '😢', label: '悲伤',     score: 1, color: '#A5A8C5' },
}

// 心情列表（用于渲染按钮，按 score 降序排列：从开心到悲伤）
const moodList = Object.entries(MOOD_INFO)
  .map(([key, info]) => ({ key, ...info }))
  .sort((a, b) => b.score - a.score)

// ─── 罗素情绪环模型（Russell's Circumplex Model of Affect）───
// 横轴 valence：-1（消极）→ +1（积极）
// 纵轴 arousal：-1（低唤醒）→ +1（高唤醒）
// tracked=true 表示该情绪在系统中已追踪（有真实打卡数据）
// moodKey 映射到后端 MOOD_INFO 的 key，用于查询本月出现次数
const CIRCUMPLEX_EMOTIONS = [
  // 第一象限（右上：积极 + 高唤醒）
  { emoji: '🤩', label: '狂喜',     valence: 0.85, arousal: 0.85, tracked: true,  moodKey: 'ecstatic' },
  { emoji: '😆', label: '兴奋',     valence: 0.65, arousal: 0.70, tracked: false },
  { emoji: '🤗', label: '激动',     valence: 0.50, arousal: 0.55, tracked: false },
  { emoji: '✨', label: '兴致高昂', valence: 0.55, arousal: 0.40, tracked: false },
  // 第二象限（左上：消极 + 高唤醒）
  { emoji: '😠', label: '暴怒',     valence: -0.80, arousal: 0.85, tracked: true,  moodKey: 'angry' },
  { emoji: '😱', label: '恐慌',     valence: -0.75, arousal: 0.65, tracked: false },
  { emoji: '😰', label: '焦虑',     valence: -0.55, arousal: 0.50, tracked: true,  moodKey: 'anxious' },
  { emoji: '😨', label: '恐惧',     valence: -0.65, arousal: 0.35, tracked: false },
  { emoji: '😤', label: '极度烦躁', valence: -0.45, arousal: 0.45, tracked: false },
  // 第三象限（左下：消极 + 低唤醒）
  { emoji: '😢', label: '悲伤',     valence: -0.70, arousal: -0.30, tracked: true,  moodKey: 'sad' },
  { emoji: '😞', label: '低落',     valence: -0.55, arousal: -0.20, tracked: false },
  { emoji: '😔', label: '压抑',     valence: -0.45, arousal: -0.45, tracked: false },
  { emoji: '😪', label: '疲惫',     valence: -0.25, arousal: -0.60, tracked: true,  moodKey: 'tired' },
  { emoji: '😩', label: '倦怠',     valence: -0.35, arousal: -0.70, tracked: false },
  { emoji: '😶', label: '空虚',     valence: -0.50, arousal: -0.55, tracked: false },
  // 第四象限（右下：积极 + 低唤醒）
  { emoji: '😊', label: '开心',     valence: 0.60, arousal: 0.25, tracked: true,  moodKey: 'happy' },
  { emoji: '😌', label: '平静',     valence: 0.45, arousal: -0.30, tracked: true,  moodKey: 'calm' },
  { emoji: '😎', label: '闲适',     valence: 0.55, arousal: -0.50, tracked: false },
  { emoji: '😇', label: '舒心',     valence: 0.40, arousal: -0.65, tracked: false },
  { emoji: '🍃', label: '恬淡平和', valence: 0.35, arousal: -0.75, tracked: false },
]

// 四象限信息
const QUADRANT_INFO = [
  { id: 'q1', label: '积极 · 高唤醒', desc: '亢奋愉悦', color: 'rgba(255, 213, 107, 0.08)' },
  { id: 'q2', label: '消极 · 高唤醒', desc: '紧张激烈', color: 'rgba(232, 154, 154, 0.08)' },
  { id: 'q3', label: '消极 · 低唤醒', desc: '低沉消沉', color: 'rgba(165, 168, 197, 0.08)' },
  { id: 'q4', label: '积极 · 低唤醒', desc: '松弛平和', color: 'rgba(168, 213, 186, 0.08)' },
]

// 将 valence/arousal 坐标转换为图表内的百分比位置
const emotionPosition = (emotion) => ({
  left: ((emotion.valence + 1) / 2) * 100,
  top: ((1 - emotion.arousal) / 2) * 100,
})

// 周一 ~ 周日
const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']

// 当前显示的年月（默认本月）
const today = new Date()
const viewYear = ref(today.getFullYear())
const viewMonth = ref(today.getMonth()) // 0-indexed

// 选中的心情列表（支持多选，存 mood key 数组，如 ['happy', 'calm']）
const selectedMoods = ref([])

// 切换心情选择（可多选）
const toggleMood = (key) => {
  const idx = selectedMoods.value.indexOf(key)
  if (idx > -1) {
    selectedMoods.value.splice(idx, 1)
  } else {
    selectedMoods.value.push(key)
  }
}

// 数据
const checkins = ref([])         // 后端 items: [{check_date, mood_emojis, moods, ...}]
const calendarLoading = ref(false)
const trend = ref([])            // 后端 items: [{date, mood_emoji, label, color, note, mood_count, avg_score}]
const currentStreak = ref(0)
const submitting = ref(false)

// 今日已记录的心情列表
const todayMoods = ref([])

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

// 今日日期字符串 YYYY-MM-DD
const todayStr = computed(() => {
  const t = new Date()
  return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`
})

// 今日中文日期
const todayLabel = computed(() => {
  const t = new Date()
  return `${t.getFullYear()}年${t.getMonth() + 1}月${t.getDate()}日`
})

// 月份标题
const monthTitle = computed(() => `${viewYear.value}年${viewMonth.value + 1}月`)

// 日历格子（含前导空格，周一为一周第一天）
const calendarCells = computed(() => {
  const year = viewYear.value
  const month = viewMonth.value
  const firstDay = new Date(year, month, 1)
  // 周一为一周第一天：getDay() 周日=0, 周一=1 ...
  let firstWeekday = firstDay.getDay() - 1
  if (firstWeekday < 0) firstWeekday = 6
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  // checkin 映射：'YYYY-MM-DD' -> [mood_key, ...]（支持一天多条）
  const checkinMap = {}
  checkins.value.forEach(c => {
    const d = c.check_date || c.date
    if (!d) return
    // 兼容新字段 mood_emojis（数组）和旧字段 mood_emoji（单值）
    if (c.mood_emojis && Array.isArray(c.mood_emojis)) {
      checkinMap[d] = c.mood_emojis
    } else if (c.mood_emoji) {
      checkinMap[d] = [c.mood_emoji]
    }
  })

  const cells = []
  // 前导空格
  for (let i = 0; i < firstWeekday; i++) {
    cells.push({ empty: true })
  }
  // 日期格
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const moodKeys = checkinMap[dateStr] || []
    const moodInfos = moodKeys.map(k => MOOD_INFO[k]).filter(Boolean)
    cells.push({
      day: d,
      date: dateStr,
      moodKeys,
      moodInfos,
      isToday: dateStr === todayStr.value,
    })
  }
  return cells
})

// 本月各心情出现次数（从 checkins 数据统计）
const moodCounts = computed(() => {
  const counts = {}
  checkins.value.forEach(c => {
    const moods = c.mood_emojis || (c.mood_emoji ? [c.mood_emoji] : [])
    moods.forEach(m => {
      counts[m] = (counts[m] || 0) + 1
    })
  })
  return counts
})

// 获取某个情绪在本月的出现次数
const emotionCount = (emotion) => {
  if (!emotion.tracked || !emotion.moodKey) return 0
  return moodCounts.value[emotion.moodKey] || 0
}

// 本月总打卡数
const totalCheckins = computed(() => {
  return Object.values(moodCounts.value).reduce((sum, n) => sum + n, 0)
})

// 选中的情绪（点击交互）
const selectedEmotion = ref(null)

const onEmotionClick = (emotion) => {
  if (selectedEmotion.value?.label === emotion.label) {
    selectedEmotion.value = null
  } else {
    selectedEmotion.value = emotion
  }
}

const closeEmotionPopup = () => {
  selectedEmotion.value = null
}

// 上一月
const prevMonth = () => {
  if (viewMonth.value === 0) {
    viewMonth.value = 11
    viewYear.value--
  } else {
    viewMonth.value--
  }
  fetchCalendar()
}

// 下一月
const nextMonth = () => {
  if (viewMonth.value === 11) {
    viewMonth.value = 0
    viewYear.value++
  } else {
    viewMonth.value++
  }
  fetchCalendar()
}

// 拉取日历数据
const fetchCalendar = async () => {
  calendarLoading.value = true
  try {
    const res = await api.get('/mood/calendar', {
      params: { year: viewYear.value, month: viewMonth.value + 1 },
    })
    // 后端返回 { year, month, items: [...] }；兼容旧字段 checkins
    checkins.value = res?.items || res?.checkins || []
    // 若当前月包含今天，拉取今日已记录的心情
    const t = new Date()
    if (t.getFullYear() === viewYear.value && t.getMonth() === viewMonth.value) {
      await fetchTodayMoods()
    }
  } catch (e) {
    showToast(e.message || '日历加载失败', 2500)
  } finally {
    calendarLoading.value = false
  }
}

// 拉取今日已记录的心情
const fetchTodayMoods = async () => {
  try {
    const res = await api.get('/mood/today')
    if (res?.checked_in && res?.moods) {
      todayMoods.value = res.moods.map(m => m.mood_emoji).filter(Boolean)
    } else {
      todayMoods.value = []
    }
  } catch {
    todayMoods.value = []
  }
}

// 拉取 30 天趋势
const fetchTrend = async () => {
  try {
    const res = await api.get('/mood/trend', { params: { days: 30 } })
    trend.value = res?.items || res?.trend || []
    currentStreak.value = res?.current_streak || 0
  } catch (e) {
    // 趋势失败静默
  }
}

// 今日打卡（支持多选）
const doCheckin = async () => {
  if (selectedMoods.value.length === 0) {
    showToast('先选一个或多个今天的心情吧 🌿', 2200)
    return
  }
  if (submitting.value) return
  submitting.value = true
  const moods = [...selectedMoods.value]
  try {
    // 批量提交多个心情
    const res = await api.post('/mood/checkin/batch', {
      mood_emojis: moods,
    })
    // 更新露水
    if (typeof res?.new_total_energy === 'number') {
      userStore.updateEnergy(res.new_total_energy)
    }
    // v2.4.2：更新落叶余额 + 徽章解锁 toast
    if (typeof res?.leaves_balance === 'number') {
      userStore.updateResources({ leaves: res.leaves_balance })
    }
    if (Array.isArray(res?.new_badges) && res.new_badges.length > 0) {
      const badgeTexts = res.new_badges.map(b => `${b.image} 解锁徽章「${b.name}」· 赠 ${res.new_leaves} 落叶`)
      showToast(badgeTexts.join('  '), 4000)
      // 徽章 toast 优先，跳过治愈语
      selectedMoods.value = []
      await fetchCalendar()
      await fetchTrend()
      await fetchTodayMoods()
      return
    }
    // 刷新数据
    await fetchCalendar()
    await fetchTrend()
    // 清空选择
    selectedMoods.value = []
    // 更新今日心情列表
    await fetchTodayMoods()
    // 请求 AI 治愈语（用第一个心情）
    const firstMoodKey = moods[0]
    const firstMoodInfo = MOOD_INFO[firstMoodKey]
    let healingShown = false
    try {
      const aiRes = await api.post('/ai/healing', {
        mood_emoji: firstMoodKey,
        mood_label: firstMoodInfo.label,
      })
      if (aiRes?.available && aiRes?.text) {
        showToast(aiRes.text, 3000)
        healingShown = true
      }
    } catch (aiErr) {
      // AI 失败静默
    }
    if (!healingShown) {
      const moodEmojis = moods.map(k => MOOD_INFO[k]?.emoji).join(' ')
      showToast(`今日心情已记下 ${moodEmojis}`, 2200)
    }
  } catch (e) {
    showToast(e.message || '打卡失败，请稍后再试', 2500)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchCalendar()
  fetchTrend()
  nextTick(() => {
    // 注意：不要在 from 里写 opacity:0 / scale:0 —— 动画被中断（如切后台、路由切换）
    // 时元素会永久卡在不可见状态（v2.4.4 的「透明 bug」同类根因），只保留位移动画
    gsap.from('.mood-header', { y: -20, duration: 0.6, ease: 'power2.out' })
    gsap.from('.mood-picker__btn', {
      y: 20, duration: 0.5, stagger: 0.06, ease: 'power3.out', delay: 0.1,
    })
    gsap.from('.calendar-nav', { y: 16, duration: 0.5, ease: 'power2.out', delay: 0.2 })
    gsap.from('.calendar-cell:not(.calendar-cell--empty)', {
      y: 16, duration: 0.45, stagger: 0.012, ease: 'power2.out', delay: 0.25,
    })
    gsap.from('.circumplex-section', {
      y: 20, duration: 0.6, ease: 'power2.out', delay: 0.4,
    })
    gsap.from('.circumplex-emotion', {
      y: 10, duration: 0.4, stagger: 0.04, ease: 'back.out(1.7)', delay: 0.6,
    })
  })
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="mood-calendar-view">
    <!-- 顶部标题 -->
    <header class="mood-header">
      <h1 class="mood-header__title">情绪日历</h1>
      <p class="mood-header__verse">"把每一天的心情，画进日历里"</p>
      <p v-if="currentStreak > 0" class="mood-header__streak">
        已连续记录 {{ currentStreak }} 天 · 继续坚持下去 🌿
      </p>
    </header>

    <!-- 顶部心情打卡区 -->
    <section class="mood-picker card">
      <div class="mood-picker__date">今日 · {{ todayLabel }}</div>
      <p class="mood-picker__hint">此刻你感觉怎么样？可以多选哦</p>
      <div class="mood-picker__row">
        <button
          v-for="m in moodList"
          :key="m.key"
          class="mood-picker__btn"
          :class="{ 'is-selected': selectedMoods.includes(m.key) }"
          @click="toggleMood(m.key)"
          :aria-label="m.label"
          :title="m.label"
        >
          <span class="mood-picker__btn-emoji">{{ m.emoji }}</span>
          <span class="mood-picker__btn-label">{{ m.label }}</span>
        </button>
      </div>
      <!-- 今日已记录的心情 -->
      <div v-if="todayMoods.length > 0" class="mood-picker__today">
        <span class="mood-picker__today-label">今日已记：</span>
        <span
          v-for="key in todayMoods"
          :key="key"
          class="mood-picker__today-emoji"
          :title="MOOD_INFO[key]?.label"
        >{{ MOOD_INFO[key]?.emoji }}</span>
      </div>
      <button
        class="btn btn--primary mood-picker__submit"
        :disabled="submitting || selectedMoods.length === 0"
        @click="doCheckin"
      >
        {{ submitting ? '记录中…' : `今日打卡${selectedMoods.length > 0 ? ` (${selectedMoods.length})` : ''}` }}
      </button>
    </section>

    <!-- 月份切换 -->
    <div class="calendar-nav">
      <button class="calendar-nav__btn" @click="prevMonth" aria-label="上一月">‹</button>
      <div class="calendar-nav__title">{{ monthTitle }}</div>
      <button class="calendar-nav__btn" @click="nextMonth" aria-label="下一月">›</button>
    </div>

    <!-- 日历网格 -->
    <section class="calendar card">
      <div class="calendar__weekdays">
        <div v-for="w in WEEKDAYS" :key="w" class="calendar__weekday">周{{ w }}</div>
      </div>
      <div class="calendar__grid">
        <div
          v-for="(cell, i) in calendarCells"
          :key="i"
          class="calendar-cell"
          :class="{
            'calendar-cell--empty': cell.empty,
            'calendar-cell--today': cell.isToday,
            'calendar-cell--has-mood': cell.moodKeys?.length > 0,
          }"
          :title="cell.moodInfos?.length ? `${cell.date} · ${cell.moodInfos.map(m => m.label).join('、')}` : (cell.date || '')"
        >
          <template v-if="!cell.empty">
            <div v-if="cell.moodInfos?.length > 0" class="calendar-cell__emojis">
              <span
                v-for="(info, idx) in cell.moodInfos.slice(0, 3)"
                :key="idx"
                class="calendar-cell__emoji"
              >{{ info.emoji }}</span>
              <span v-if="cell.moodInfos.length > 3" class="calendar-cell__more">+{{ cell.moodInfos.length - 3 }}</span>
            </div>
            <div v-else class="calendar-cell__day">{{ cell.day }}</div>
          </template>
        </div>
      </div>
      <!-- 心情图例 -->
      <div class="calendar__legend">
        <span
          v-for="m in moodList"
          :key="m.key"
          class="calendar__legend-item"
          :title="m.label"
        >
          <span class="calendar__legend-emoji">{{ m.emoji }}</span>
          <span class="calendar__legend-label">{{ m.label }}</span>
        </span>
      </div>
    </section>

    <!-- 近 30 天心情趋势柱状图 -->
    <section class="trend-section card" v-if="trend.length">
      <h2 class="trend-section__title">近 30 天心情趋势</h2>
      <p class="trend-section__subtitle">
        柱子越高，代表那天整体心情越好 · 一天多条记录取平均分
      </p>
      <div class="trend-chart">
        <div
          v-for="t in trend"
          :key="t.date"
          class="trend-bar-col"
          :title="t.label ? `${t.date} · ${t.label}${t.mood_count > 1 ? ` ×${t.mood_count}` : ''}` : `${t.date} · 未记录`"
        >
          <!-- 当日主心情 emoji 悬浮柱顶 -->
          <div
            v-if="t.mood_emoji && MOOD_INFO[t.mood_emoji]"
            class="trend-bar__emoji"
          >{{ MOOD_INFO[t.mood_emoji].emoji }}</div>
          <div
            class="trend-bar"
            :class="{ 'trend-bar--empty': !t.avg_score }"
            :style="t.avg_score ? {
              height: `${(t.avg_score / 5) * 100}%`,
              background: `linear-gradient(180deg, ${t.color || '#B8A590'} 0%, ${(t.color || '#B8A590')}CC 100%)`,
            } : {}"
          ></div>
        </div>
      </div>
      <div class="trend-axis">
        <span>{{ trend[0]?.date?.slice(5) }}</span>
        <span>今天</span>
      </div>
    </section>

    <!-- 情绪环状模型（Russell's Circumplex Model） -->
    <section class="circumplex-section card">
      <h2 class="circumplex-section__title">情绪环状图</h2>
      <p class="circumplex-section__subtitle">
        基于「罗素情绪环模型」· 横轴为效价（消极→积极），纵轴为唤醒度（平静→激烈）
        <span class="circumplex-section__total">本月共记录 {{ totalCheckins }} 次</span>
      </p>

      <div class="circumplex-chart" @click.self="closeEmotionPopup">
        <!-- 四象限背景 -->
        <div class="circumplex-quadrant circumplex-quadrant--q1" :style="{ background: QUADRANT_INFO[0].color }">
          <span class="circumplex-quadrant__label">{{ QUADRANT_INFO[0].desc }}</span>
        </div>
        <div class="circumplex-quadrant circumplex-quadrant--q2" :style="{ background: QUADRANT_INFO[1].color }">
          <span class="circumplex-quadrant__label">{{ QUADRANT_INFO[1].desc }}</span>
        </div>
        <div class="circumplex-quadrant circumplex-quadrant--q3" :style="{ background: QUADRANT_INFO[2].color }">
          <span class="circumplex-quadrant__label">{{ QUADRANT_INFO[2].desc }}</span>
        </div>
        <div class="circumplex-quadrant circumplex-quadrant--q4" :style="{ background: QUADRANT_INFO[3].color }">
          <span class="circumplex-quadrant__label">{{ QUADRANT_INFO[3].desc }}</span>
        </div>

        <!-- 坐标轴 -->
        <div class="circumplex-axis circumplex-axis--x"></div>
        <div class="circumplex-axis circumplex-axis--y"></div>

        <!-- 轴标注 -->
        <div class="circumplex-axis-label circumplex-axis-label--x-pos">积极</div>
        <div class="circumplex-axis-label circumplex-axis-label--x-neg">消极</div>
        <div class="circumplex-axis-label circumplex-axis-label--y-pos">高唤醒</div>
        <div class="circumplex-axis-label circumplex-axis-label--y-neg">低唤醒</div>

        <!-- 情绪 emoji -->
        <button
          v-for="(emotion, i) in CIRCUMPLEX_EMOTIONS"
          :key="i"
          class="circumplex-emotion"
          :class="{
            'circumplex-emotion--tracked': emotion.tracked,
            'circumplex-emotion--active': selectedEmotion?.label === emotion.label,
          }"
          :style="{
            left: emotionPosition(emotion).left + '%',
            top: emotionPosition(emotion).top + '%',
          }"
          @click.stop="onEmotionClick(emotion)"
          :aria-label="emotion.label"
          :title="emotion.label"
        >
          <span class="circumplex-emotion__emoji">{{ emotion.emoji }}</span>
          <span v-if="emotion.tracked && emotionCount(emotion) > 0" class="circumplex-emotion__badge">
            {{ emotionCount(emotion) }}
          </span>
        </button>
      </div>

      <!-- 点击弹出详情 -->
      <transition name="circumplex-popup">
        <div v-if="selectedEmotion" class="circumplex-detail">
          <div class="circumplex-detail__emoji">{{ selectedEmotion.emoji }}</div>
          <div class="circumplex-detail__body">
            <div class="circumplex-detail__label">{{ selectedEmotion.label }}</div>
            <div v-if="selectedEmotion.tracked" class="circumplex-detail__count">
              本月出现 <strong>{{ emotionCount(selectedEmotion) }}</strong> 次
            </div>
            <div v-else class="circumplex-detail__count circumplex-detail__count--muted">
              该情绪暂未开放打卡记录
            </div>
          </div>
          <button class="circumplex-detail__close" @click="closeEmotionPopup" aria-label="关闭">×</button>
        </div>
      </transition>

      <!-- 图例 -->
      <div class="circumplex-legend">
        <span class="circumplex-legend__item">
          <span class="circumplex-legend__dot circumplex-legend__dot--tracked"></span>
          已追踪（可打卡）
        </span>
        <span class="circumplex-legend__item">
          <span class="circumplex-legend__dot"></span>
          参考情绪
        </span>
      </div>
    </section>

    <!-- toast 轻提示 -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.mood-calendar-view {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* 平板紧凑 */
@media (min-width: 769px) and (max-width: 1024px) {
  .mood-calendar-view {
    padding: 28px 20px 72px;
  }
}

/* 顶部标题 */
.mood-header {
  text-align: center;
  margin-bottom: 28px;
}
.mood-header__title {
  font-family: var(--font-serif, serif);
  font-size: 30px;
  font-weight: 500;
  letter-spacing: 0.1em;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
}
.mood-header__verse {
  font-family: var(--font-serif, serif);
  font-style: italic;
  font-size: 14px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0;
  letter-spacing: 0.05em;
}
.mood-header__streak {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-accent-dark, #8B7B5E);
  letter-spacing: 0.05em;
}

/* 心情打卡区 */
.mood-picker {
  text-align: center;
  padding: 28px 24px;
  margin-bottom: 36px;
  background: linear-gradient(135deg, rgba(232, 184, 197, 0.22) 0%, rgba(168, 197, 232, 0.22) 100%);
}
.mood-picker__date {
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}
.mood-picker__hint {
  font-family: var(--font-serif, serif);
  font-size: 15px;
  color: var(--color-text-secondary, #5C4F3E);
  margin: 0 0 20px;
  letter-spacing: 0.05em;
}
.mood-picker__row {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}
.mood-picker__btn {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  border: 2px solid transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  transition: all 0.3s var(--ease-soft, ease);
  cursor: pointer;
  backdrop-filter: blur(8px);
  overflow: visible;
}
.mood-picker__btn:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md, 0 6px 20px rgba(139, 123, 94, 0.1));
}
.mood-picker__btn-emoji {
  font-size: 30px;
  line-height: 1;
}
.mood-picker__btn-label {
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.05em;
  white-space: nowrap;
}
.mood-picker__btn.is-selected {
  background: linear-gradient(135deg, rgba(232, 184, 197, 0.45) 0%, rgba(168, 197, 232, 0.45) 100%);
  border-color: var(--color-accent, #B8A590);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(184, 165, 144, 0.28);
}
.mood-picker__today {
  margin-bottom: 18px;
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
}
.mood-picker__today-label {
  margin-right: 4px;
}
.mood-picker__today-emoji {
  font-size: 18px;
  margin-right: 2px;
}
.mood-picker__submit {
  min-width: 140px;
}
.mood-picker__submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 月份切换 */
.calendar-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 18px;
}
.calendar-nav__btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  color: var(--color-text-secondary, #5C4F3E);
  font-size: 20px;
  line-height: 1;
  display: grid;
  place-items: center;
  transition: all 0.25s var(--ease-soft, ease);
  cursor: pointer;
}
.calendar-nav__btn:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: scale(1.05);
  color: var(--color-accent-dark, #8B7B5E);
}
.calendar-nav__title {
  font-family: var(--font-serif, serif);
  font-size: 20px;
  color: var(--color-text-primary, #3D3327);
  letter-spacing: 0.1em;
  min-width: 140px;
  text-align: center;
}

/* 日历 */
.calendar {
  padding: 20px;
  margin-bottom: 40px;
}
.calendar__weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  margin-bottom: 10px;
}
.calendar__weekday {
  text-align: center;
  font-family: var(--font-serif, serif);
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.05em;
  padding: 6px 0;
}
.calendar__grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}
.calendar-cell {
  aspect-ratio: 1;
  border-radius: var(--radius-md, 14px);
  background: rgba(255, 255, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.25s var(--ease-soft, ease);
  overflow: hidden;
}
.calendar-cell--empty {
  background: transparent;
}
.calendar-cell--today {
  background: linear-gradient(135deg, rgba(232, 184, 197, 0.22) 0%, rgba(168, 197, 232, 0.22) 100%);
  box-shadow: inset 0 0 0 2px var(--color-accent, #B8A590);
}
.calendar-cell--has-mood {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.7) 0%, rgba(255, 246, 240, 0.7) 100%);
}
.calendar-cell__day {
  font-family: var(--font-serif, serif);
  font-size: 14px;
  color: var(--color-text-muted, #8B7B5E);
}
.calendar-cell__emojis {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1px;
  padding: 2px;
}
.calendar-cell__emoji {
  font-size: 20px;
  line-height: 1;
}
.calendar-cell__more {
  font-size: 10px;
  color: var(--color-text-muted, #8B7B5E);
}

/* 心情图例：让所有 emoji 都能完整显示 */
.calendar__legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 14px 18px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px dashed var(--color-border, rgba(139, 123, 94, 0.15));
}
.calendar__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.05em;
}
.calendar__legend-emoji {
  font-size: 18px;
  line-height: 1;
}
.calendar__legend-label {
  font-family: var(--font-serif, serif);
}

/* 近 30 天趋势柱状图 */
.trend-section {
  padding: 24px;
  margin-bottom: 40px;
}
.trend-section__title {
  font-family: var(--font-serif, serif);
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
  letter-spacing: 0.05em;
}
.trend-section__subtitle {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0 0 18px;
  letter-spacing: 0.03em;
}
.trend-chart {
  display: flex;
  align-items: stretch;
  gap: 3px;
  height: 150px;
  padding: 20px 2px 0; /* 顶部留出 emoji 空间 */
}
.trend-bar-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  gap: 3px;
}
.trend-bar {
  width: 100%;
  max-width: 18px;
  min-height: 4px;
  border-radius: 4px 4px 2px 2px;
  transition: height 0.4s var(--ease-soft, ease);
}
.trend-bar--empty {
  height: 3px !important;
  min-height: 3px;
  background: rgba(139, 123, 94, 0.15);
}
.trend-bar__emoji {
  font-size: 11px;
  line-height: 1;
  filter: saturate(0.9);
}
.trend-axis {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.05em;
}

/* 情绪环状图（Russell's Circumplex Model） */
.circumplex-section {
  padding: 24px;
}
.circumplex-section__title {
  font-family: var(--font-serif, serif);
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary, #3D3327);
  margin: 0 0 6px;
  letter-spacing: 0.05em;
}
.circumplex-section__subtitle {
  font-size: 13px;
  color: var(--color-text-muted, #8B7B5E);
  margin: 0 0 20px;
  line-height: 1.6;
}
.circumplex-section__total {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 10px;
  border-radius: 12px;
  background: rgba(184, 165, 144, 0.12);
  color: var(--color-accent-dark, #8B7B5E);
  font-size: 12px;
}

/* 四象限图表容器 */
.circumplex-chart {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  max-width: 480px;
  margin: 0 auto 20px;
  border-radius: var(--radius-lg, 20px);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.1));
}

/* 四象限背景 */
.circumplex-quadrant {
  position: absolute;
  width: 50%;
  height: 50%;
  display: flex;
  padding: 8px 10px;
}
.circumplex-quadrant--q1 { top: 0; right: 0; align-items: flex-start; justify-content: flex-end; }
.circumplex-quadrant--q2 { top: 0; left: 0; align-items: flex-start; justify-content: flex-start; }
.circumplex-quadrant--q3 { bottom: 0; left: 0; align-items: flex-end; justify-content: flex-start; }
.circumplex-quadrant--q4 { bottom: 0; right: 0; align-items: flex-end; justify-content: flex-end; }
.circumplex-quadrant__label {
  font-family: var(--font-serif, serif);
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  opacity: 0.6;
  letter-spacing: 0.05em;
}

/* 坐标轴 */
.circumplex-axis {
  position: absolute;
  background: var(--color-border, rgba(139, 123, 94, 0.2));
  pointer-events: none;
}
.circumplex-axis--x {
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
}
.circumplex-axis--y {
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
}

/* 轴标注 */
.circumplex-axis-label {
  position: absolute;
  font-family: var(--font-serif, serif);
  font-size: 11px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.05em;
  pointer-events: none;
  z-index: 2;
}
.circumplex-axis-label--x-pos { right: 8px; top: calc(50% + 6px); }
.circumplex-axis-label--x-neg { left: 8px; top: calc(50% + 6px); }
.circumplex-axis-label--y-pos { top: 6px; left: calc(50% + 8px); }
.circumplex-axis-label--y-neg { bottom: 6px; left: calc(50% + 8px); }

/* 情绪 emoji 节点 */
.circumplex-emotion {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s var(--ease-soft, ease);
  backdrop-filter: blur(4px);
  z-index: 3;
  padding: 0;
}
.circumplex-emotion__emoji {
  font-size: 22px;
  line-height: 1;
}
.circumplex-emotion:hover {
  transform: translate(-50%, -50%) scale(1.18);
  box-shadow: 0 4px 14px rgba(139, 123, 94, 0.2);
  z-index: 5;
}
.circumplex-emotion--tracked {
  border-color: var(--color-accent, #B8A590);
}
.circumplex-emotion--active {
  transform: translate(-50%, -50%) scale(1.2);
  border-color: var(--color-accent-dark, #8B7B5E);
  box-shadow: 0 4px 18px rgba(184, 165, 144, 0.4);
  background: rgba(255, 255, 255, 0.95);
  z-index: 6;
}
/* 出现次数角标 */
.circumplex-emotion__badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--color-accent, #B8A590);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* 点击弹出详情 */
.circumplex-detail {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border-radius: var(--radius-md, 14px);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 246, 240, 0.9) 100%);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.15));
  margin-bottom: 16px;
}
.circumplex-detail__emoji {
  font-size: 32px;
  line-height: 1;
  flex-shrink: 0;
}
.circumplex-detail__body {
  flex: 1;
}
.circumplex-detail__label {
  font-family: var(--font-serif, serif);
  font-size: 16px;
  color: var(--color-text-primary, #3D3327);
  margin-bottom: 2px;
  letter-spacing: 0.05em;
}
.circumplex-detail__count {
  font-size: 13px;
  color: var(--color-text-secondary, #5C4F3E);
}
.circumplex-detail__count strong {
  color: var(--color-accent-dark, #8B7B5E);
  font-size: 16px;
  font-weight: 600;
}
.circumplex-detail__count--muted {
  color: var(--color-text-muted, #8B7B5E);
  font-style: italic;
}
.circumplex-detail__close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(139, 123, 94, 0.1);
  color: var(--color-text-muted, #8B7B5E);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  display: grid;
  place-items: center;
  transition: all 0.2s;
  flex-shrink: 0;
}
.circumplex-detail__close:hover {
  background: rgba(139, 123, 94, 0.2);
  color: var(--color-text-primary, #3D3327);
}

/* 弹出动画 */
.circumplex-popup-enter-active,
.circumplex-popup-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}
.circumplex-popup-enter-from,
.circumplex-popup-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 图例 */
.circumplex-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 4px;
}
.circumplex-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-muted, #8B7B5E);
  letter-spacing: 0.05em;
}
.circumplex-legend__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--color-border, rgba(139, 123, 94, 0.2));
}
.circumplex-legend__dot--tracked {
  border-color: var(--color-accent, #B8A590);
  border-width: 2px;
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

/* 响应式：移动端保持 7 列但缩小格子 */
@media (max-width: 768px) {
  .mood-calendar-view {
    padding: 20px 12px 60px;
  }
  .mood-header__title {
    font-size: 24px;
  }
  .mood-picker {
    padding: 22px 14px;
    margin-bottom: 28px;
  }
  .mood-picker__row {
    gap: 8px;
  }
  .mood-picker__btn {
    width: 64px;
    height: 64px;
  }
  .mood-picker__btn-emoji {
    font-size: 26px;
  }
  .mood-picker__btn-label {
    font-size: 10px;
  }
  .calendar {
    padding: 12px 8px;
  }
  .calendar__grid,
  .calendar__weekdays {
    gap: 4px;
  }
  .calendar__weekday {
    font-size: 11px;
    padding: 4px 0;
  }
  .calendar-cell__day {
    font-size: 11px;
  }
  .calendar-cell__emoji {
    font-size: 16px;
  }
  .calendar-cell__more {
    font-size: 9px;
  }
  .calendar__legend {
    gap: 10px 12px;
  }
  .calendar__legend-emoji {
    font-size: 16px;
  }
  .trend-section {
    padding: 18px 14px;
    margin-bottom: 28px;
  }
  .trend-chart {
    gap: 2px;
    height: 110px;
    padding-top: 16px;
  }
  .trend-bar {
    max-width: 12px;
    border-radius: 3px 3px 2px 2px;
  }
  .trend-bar__emoji {
    font-size: 9px;
  }
  .calendar-nav__title {
    font-size: 17px;
    min-width: 110px;
  }
  .calendar-nav__btn {
    width: 32px;
    height: 32px;
    font-size: 18px;
  }
  .circumplex-section {
    padding: 18px 14px;
  }
  .circumplex-chart {
    max-width: 100%;
  }
  .circumplex-emotion {
    width: 34px;
    height: 34px;
  }
  .circumplex-emotion__emoji {
    font-size: 18px;
  }
  .circumplex-quadrant__label {
    font-size: 10px;
  }
  .circumplex-axis-label {
    font-size: 10px;
  }
  /* toast 上移避开 tabbar */
  .toast {
    bottom: calc(90px + env(safe-area-inset-bottom));
  }
}
</style>
