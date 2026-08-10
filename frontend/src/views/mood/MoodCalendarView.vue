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

// 趋势条形数据（高度按 score/5 换算百分比；多条取平均分）
const trendBars = computed(() => {
  return trend.value.map(t => {
    const moodKey = t.mood_emoji || t.mood_type
    const info = moodKey ? MOOD_INFO[moodKey] : null
    // 优先用后端返回的 avg_score（多条记录的平均分）
    const score = t.avg_score || info?.score || 0
    return {
      date: t.date,
      score,
      moodInfo: info,
      moodCount: t.mood_count || 1,
      heightPct: score ? (score / 5) * 100 : 6,
      isEmpty: !score,
    }
  })
})

// 根据心情分数取色（治愈系雾粉/雾蓝/暖米）
const scoreColor = (score) => {
  // 支持小数分数（多条平均）
  if (score >= 4.5) return 'linear-gradient(180deg, #F5C5D0, #E8A8B8)' // 雾粉
  if (score >= 3.5) return 'linear-gradient(180deg, #F5DCC8, #E8C5A8)' // 暖米
  if (score >= 2.5) return 'linear-gradient(180deg, #EDE0D0, #D5C5A8)' // 浅米
  if (score >= 1.5) return 'linear-gradient(180deg, #C5D5E8, #A8C0D8)' // 雾蓝
  return 'linear-gradient(180deg, #A8B8D5, #8898C0)' // 深雾蓝
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
    gsap.from('.mood-header', { y: -20, opacity: 0, duration: 0.6, ease: 'power2.out' })
    gsap.from('.mood-picker__btn', {
      y: 20, opacity: 0, duration: 0.5, stagger: 0.06, ease: 'power3.out', delay: 0.1,
    })
    gsap.from('.calendar-nav', { y: 16, opacity: 0, duration: 0.5, ease: 'power2.out', delay: 0.2 })
    gsap.from('.calendar-cell:not(.calendar-cell--empty)', {
      y: 16, opacity: 0, duration: 0.45, stagger: 0.012, ease: 'power2.out', delay: 0.25,
    })
    gsap.from('.trend-bar', {
      scaleY: 0, transformOrigin: 'bottom', duration: 0.55, stagger: 0.02, ease: 'power2.out', delay: 0.5,
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
            'calendar-cell--has-mood': cell.moodKeys.length > 0,
          }"
          :title="cell.moodInfos.length ? `${cell.date} · ${cell.moodInfos.map(m => m.label).join('、')}` : (cell.date || '')"
        >
          <template v-if="!cell.empty">
            <div v-if="cell.moodInfos.length > 0" class="calendar-cell__emojis">
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

    <!-- 趋势图 -->
    <section class="trend-section card">
      <h2 class="trend-section__title">30 天心情趋势</h2>
      <p class="trend-section__subtitle">每一条小柱子，都是你那天的心情 · 一天多条记录取平均分</p>
      <div v-if="trendBars.length === 0" class="trend-section__empty">还没有趋势数据</div>
      <div v-else class="trend-chart">
        <div
          v-for="(bar, i) in trendBars"
          :key="i"
          class="trend-bar"
          :class="{ 'trend-bar--empty': bar.isEmpty }"
          :style="{ height: bar.heightPct + '%', background: bar.isEmpty ? '' : scoreColor(bar.score) }"
        >
          <div class="trend-bar__tip">
            {{ bar.date?.slice(5) }} {{ bar.moodInfo?.emoji || '·' }}
            <span v-if="bar.moodCount > 1">（{{ bar.moodCount }}条）</span>
          </div>
        </div>
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

/* 趋势图 */
.trend-section {
  padding: 24px;
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
  margin: 0 0 20px;
}
.trend-section__empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-text-muted, #8B7B5E);
  font-size: 13px;
}
.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 140px;
  padding: 0 4px;
  overflow-x: auto;
}
.trend-bar {
  flex: 1 0 8px;
  min-width: 6px;
  border-radius: 6px 6px 2px 2px;
  position: relative;
  transition: transform 0.2s var(--ease-soft, ease), filter 0.2s;
  cursor: pointer;
}
.trend-bar:hover {
  transform: translateY(-2px);
  filter: brightness(1.05);
}
.trend-bar--empty {
  background: rgba(139, 123, 94, 0.1);
}
.trend-bar__tip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(90, 70, 50, 0.92);
  color: #fff;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
  margin-bottom: 6px;
}
.trend-bar:hover .trend-bar__tip {
  opacity: 1;
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
  .calendar-nav__title {
    font-size: 17px;
    min-width: 110px;
  }
  .calendar-nav__btn {
    width: 32px;
    height: 32px;
    font-size: 18px;
  }
  .trend-section {
    padding: 18px 14px;
  }
  .trend-chart {
    height: 110px;
    gap: 2px;
  }
  /* toast 上移避开 tabbar */
  .toast {
    bottom: calc(90px + env(safe-area-inset-bottom));
  }
}
</style>
