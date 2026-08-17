<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'
import AudioVisualizer from '@/components/AudioVisualizer.vue'

const router = useRouter()

// 五音常量（用于把 western 曲目按 yin 归类展示）
const YIN_INFO = {
  gong: { name: '宫', element: '土', color: '#E8B8A8' },
  shang: { name: '商', element: '金', color: '#E8C5A8' },
  jue: { name: '角', element: '木', color: '#A8C5A0' },
  zhi: { name: '徵', element: '火', color: '#E8A8B8' },
  yu: { name: '羽', element: '水', color: '#A8B8C5' },
}

// 数据
const musics = ref([])
const loading = ref(false)
const errorMsg = ref('')

// 播放器状态
const audioEl = ref(null)
const visualizerRef = ref(null)
const visualizerConnected = ref(false)
const currentIndex = ref(-1)
const currentMusic = computed(() =>
  currentIndex.value >= 0 ? musics.value[currentIndex.value] : null
)
const isPlaying = ref(false)
const progress = ref(0)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.8)
const listenReported = ref(false)

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

// 按五音分组
const groupedMusics = computed(() => {
  const groups = {}
  musics.value.forEach(m => {
    const yin = m.yin_type || 'other'
    if (!groups[yin]) groups[yin] = []
    groups[yin].push(m)
  })
  // 按五音顺序排序
  const order = ['gong', 'shang', 'jue', 'zhi', 'yu']
  return Object.entries(groups)
    .map(([yin, list]) => ({
      yin,
      info: YIN_INFO[yin] || { name: '其他', element: '', color: '#B8A590' },
      items: list,
    }))
    .sort((a, b) => order.indexOf(a.yin) - order.indexOf(b.yin))
})

// 时间格式化
const formatTime = (sec) => {
  if (!sec || isNaN(sec)) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
const formatDuration = (d) => (d ? formatTime(d) : '--:--')

// 拉取 western 类曲目
const fetchMusics = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    // 后端 /api/music 支持 ?category=western 过滤
    const res = await api.get('/music', { params: { category: 'western' } })
    // api.get 返回数组
    musics.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (e) {
    errorMsg.value = '曲目加载失败，请稍后再试'
  } finally {
    loading.value = false
  }
}

// 播放
const playIndex = (idx) => {
  if (idx < 0 || idx >= musics.value.length) return
  currentIndex.value = idx
  listenReported.value = false
  const audio = audioEl.value
  if (!audio) return
  if (!visualizerConnected.value && visualizerRef.value) {
    visualizerRef.value.connect(audio)
    visualizerConnected.value = true
  }
  audio.load()
  audio.volume = volume.value
  audio.play().then(() => {
    isPlaying.value = true
  }).catch(() => {
    isPlaying.value = false
  })
}

const togglePlay = () => {
  const audio = audioEl.value
  if (!audio || !currentMusic.value) return
  if (audio.paused) {
    audio.play()
    isPlaying.value = true
  } else {
    audio.pause()
    isPlaying.value = false
  }
}

const playPrev = () => {
  if (musics.value.length === 0) return
  const idx = currentIndex.value <= 0 ? musics.value.length - 1 : currentIndex.value - 1
  playIndex(idx)
}
const playNext = () => {
  if (musics.value.length === 0) return
  const idx = (currentIndex.value + 1) % musics.value.length
  playIndex(idx)
}

const onTimeUpdate = () => {
  const audio = audioEl.value
  if (!audio) return
  currentTime.value = audio.currentTime
  duration.value = audio.duration || 0
  if (duration.value > 0) {
    progress.value = audio.currentTime / audio.duration
    if (!listenReported.value && progress.value >= 0.9) {
      reportListenComplete()
    }
  }
}

const onEnded = () => {
  isPlaying.value = false
  progress.value = 0
  currentTime.value = 0
}

const seek = (e) => {
  const audio = audioEl.value
  if (!audio || !audio.duration) return
  const rect = e.currentTarget.getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  audio.currentTime = ratio * audio.duration
  progress.value = ratio
}

const onVolumeChange = (e) => {
  volume.value = parseFloat(e.target.value)
  if (audioEl.value) {
    audioEl.value.volume = volume.value
  }
}

// 上报聆听完成（同 MusicDetailView 逻辑）
const reportListenComplete = async () => {
  if (!currentMusic.value) return
  listenReported.value = true
  try {
    const res = await api.post('/music/listen-complete', {
      music_id: currentMusic.value.id,
      progress: Math.round(progress.value * 100),
    })
    if (res?.granted) {
      showToast('+1 露水 💧')
    }
  } catch {
    // 静默
  }
}

const stopAudio = () => {
  if (audioEl.value) {
    audioEl.value.pause()
    audioEl.value.currentTime = 0
  }
  isPlaying.value = false
  progress.value = 0
  currentTime.value = 0
  currentIndex.value = -1
  listenReported.value = false
}

// 获取当前播放曲目在分组中的全局 index
const getGlobalIndex = (groupIdx, itemIdx) => {
  let count = 0
  const groups = groupedMusics.value
  for (let i = 0; i < groupIdx; i++) {
    count += groups[i].items.length
  }
  return count + itemIdx
}

const goBack = () => {
  stopAudio()
  if (window.history.length > 1) router.back()
  else router.push('/music')
}

onMounted(() => {
  fetchMusics()
  nextTick(() => {
    gsap.from('.western-header', { y: -20, duration: 0.6, ease: 'power2.out' })
    if (audioEl.value) audioEl.value.volume = volume.value
  })
})

onBeforeUnmount(() => {
  stopAudio()
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="western-view">
    <!-- 顶部 -->
    <header class="western-header">
      <button class="back-btn" @click="goBack">← 回琴音疗心</button>
      <div class="western-header__inner">
        <div class="western-header__glyph">🎻</div>
        <div class="western-header__text">
          <h1 class="western-header__title">古琴弹西洋</h1>
          <p class="western-header__desc">用古琴演绎西洋旋律 · 中西合璧</p>
          <div class="western-header__meta">
            <span>共 {{ musics.length }} 首改编曲目</span>
          </div>
        </div>
      </div>
    </header>

    <!-- 音波可视化（当前播放时显示） -->
    <section v-if="currentMusic" class="visualizer-wrap">
      <AudioVisualizer
        ref="visualizerRef"
        :yin-key="currentMusic.yin_type"
        :is-playing="isPlaying"
        :progress="progress"
        height="100px"
      />
    </section>

    <!-- 加载/错误/空 -->
    <div v-if="loading && !musics.length" class="empty-state">曲目加载中…</div>
    <div v-else-if="errorMsg" class="empty-state">{{ errorMsg }}</div>
    <div v-else-if="!musics.length" class="empty-state">还没有古琴弹西洋曲目</div>

    <!-- 按五音分组展示 -->
    <section v-else class="groups">
      <div
        v-for="(g, gi) in groupedMusics"
        :key="g.yin"
        class="group"
      >
        <div class="group__head">
          <span class="group__dot" :style="{ background: g.info.color }"></span>
          <span class="group__name">{{ g.info.name }}音</span>
          <span class="group__element" v-if="g.info.element">· {{ g.info.element }}行</span>
          <span class="group__count">{{ g.items.length }} 首</span>
        </div>
        <ul class="track-list">
          <li
            v-for="(m, ii) in g.items"
            :key="m.id"
            class="track-item"
            :class="{ 'is-active': getGlobalIndex(gi, ii) === currentIndex }"
            @click="playIndex(getGlobalIndex(gi, ii))"
          >
            <div class="track-item__index">
              <span v-if="getGlobalIndex(gi, ii) === currentIndex && isPlaying">♪</span>
              <span v-else>{{ String(ii + 1).padStart(2, '0') }}</span>
            </div>
            <div class="track-item__main">
              <div class="track-item__title">{{ m.title }}</div>
              <div class="track-item__tags">
                <span v-for="t in (m.tags || [])" :key="t" class="track-tag">{{ t }}</span>
              </div>
            </div>
            <div class="track-item__duration">{{ formatDuration(m.duration) }}</div>
          </li>
        </ul>
      </div>
    </section>

    <!-- 底部播放器 -->
    <footer v-if="currentMusic" class="player">
      <div class="player__inner">
        <div class="player__info">
          <div class="player__title">{{ currentMusic.title }}</div>
          <div class="player__sub">
            {{ YIN_INFO[currentMusic.yin_type]?.name || '' }}音 · {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
          </div>
        </div>
        <div class="player__controls">
          <button class="ctrl-btn" @click="playPrev" aria-label="上一首">⏮</button>
          <button class="ctrl-btn ctrl-btn--play" @click="togglePlay" aria-label="播放/暂停">
            {{ isPlaying ? '⏸' : '▶' }}
          </button>
          <button class="ctrl-btn" @click="playNext" aria-label="下一首">⏭</button>
        </div>
        <div class="player__progress" @click="seek">
          <div class="player__progress-bar" :style="{ width: (progress * 100) + '%' }"></div>
        </div>
        <div class="player__volume">
          <span class="player__volume-icon">🔈</span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            :value="volume"
            @input="onVolumeChange"
            class="player__volume-slider"
          />
        </div>
      </div>
    </footer>

    <audio
      ref="audioEl"
      :src="currentMusic?.audio_url || ''"
      @timeupdate="onTimeUpdate"
      @ended="onEnded"
      @play="isPlaying = true"
      @pause="isPlaying = false"
    ></audio>

    <!-- toast -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.western-view {
  min-height: 100vh;
  min-height: 100dvh;
  padding-bottom: 140px;
}

/* 顶部 */
.western-header {
  background: linear-gradient(160deg, rgba(168, 197, 232, 0.4), rgba(232, 184, 168, 0.3) 60%, rgba(255, 255, 255, 0.7));
  padding: 24px 24px 36px;
  border-bottom-left-radius: 32px;
  border-bottom-right-radius: 32px;
  box-shadow: 0 10px 30px rgba(150, 130, 110, 0.1);
}
.back-btn {
  font-size: 13px;
  color: rgba(90, 70, 50, 0.7);
  margin-bottom: 16px;
  padding: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: color 0.2s;
}
.back-btn:hover {
  color: rgba(90, 70, 50, 0.9);
}
.western-header__inner {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 24px;
}
.western-header__glyph {
  font-size: 64px;
  line-height: 1;
  flex-shrink: 0;
  filter: drop-shadow(0 4px 12px rgba(168, 197, 232, 0.5));
}
.western-header__title {
  font-family: var(--font-serif, serif);
  font-size: 28px;
  color: rgba(90, 70, 50, 0.9);
  margin: 0 0 6px;
  font-weight: 500;
  letter-spacing: 0.1em;
}
.western-header__desc {
  font-size: 14px;
  color: rgba(90, 70, 50, 0.75);
  margin: 0 0 8px;
  line-height: 1.6;
}
.western-header__meta {
  font-size: 12px;
  color: rgba(90, 70, 50, 0.6);
}

/* 可视化 */
.visualizer-wrap {
  max-width: 1000px;
  margin: 22px auto 0;
  padding: 0 24px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 24px;
  color: var(--color-text-secondary, #8a7a6a);
  font-size: 14px;
}

/* 分组 */
.groups {
  max-width: 1000px;
  margin: 28px auto 0;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.group__head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-serif, serif);
  font-size: 15px;
  color: var(--color-text-primary, #5a4a3a);
  margin-bottom: 12px;
  letter-spacing: 0.05em;
}
.group__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.group__name {
  font-weight: 500;
}
.group__element {
  font-size: 12px;
  color: var(--color-text-muted, #8a7a6a);
}
.group__count {
  font-size: 11px;
  color: var(--color-text-muted, #8a7a6a);
  margin-left: auto;
}

/* 曲目列表 */
.track-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.track-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 16px;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
  backdrop-filter: blur(6px);
}
.track-item:hover {
  background: rgba(255, 255, 255, 0.85);
  transform: translateX(2px);
}
.track-item.is-active {
  background: linear-gradient(135deg, rgba(168, 197, 232, 0.3), rgba(255, 255, 255, 0.6));
}
.track-item__index {
  font-family: var(--font-serif, serif);
  font-size: 16px;
  color: rgba(90, 70, 50, 0.6);
  width: 32px;
  text-align: center;
  flex-shrink: 0;
}
.track-item.is-active .track-item__index {
  color: rgba(90, 70, 50, 0.9);
}
.track-item__main {
  flex: 1;
  min-width: 0;
}
.track-item__title {
  font-size: 15px;
  color: var(--color-text-primary, #5a4a3a);
  margin-bottom: 4px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.track-item__tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.track-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.5);
  color: rgba(90, 70, 50, 0.6);
  border: 1px solid rgba(200, 180, 160, 0.2);
}
.track-item__duration {
  font-size: 13px;
  color: rgba(90, 70, 50, 0.6);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

/* 底部播放器 */
.player {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border-top: 1px solid rgba(200, 180, 160, 0.2);
  z-index: 50;
  box-shadow: 0 -6px 24px rgba(150, 130, 110, 0.1);
}
.player__inner {
  max-width: 1000px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  gap: 18px;
}
.player__info {
  flex: 0 0 auto;
  min-width: 160px;
  max-width: 240px;
}
.player__title {
  font-size: 14px;
  color: var(--color-text-primary, #5a4a3a);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.player__sub {
  font-size: 11px;
  color: var(--color-text-secondary, #8a7a6a);
  margin-top: 2px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.player__controls {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ctrl-btn {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(200, 180, 160, 0.3);
  color: var(--color-text-primary, #5a4a3a);
  width: 34px;
  height: 34px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, transform 0.2s;
  font-family: inherit;
}
.ctrl-btn:hover {
  background: rgba(255, 255, 255, 1);
  transform: scale(1.05);
}
.ctrl-btn--play {
  background: linear-gradient(135deg, rgba(168, 197, 232, 0.7), rgba(255, 255, 255, 0.6));
  color: rgba(90, 70, 50, 0.9);
  width: 42px;
  height: 42px;
  border: none;
  font-size: 16px;
}
.player__progress {
  flex: 1;
  height: 6px;
  background: rgba(200, 180, 160, 0.2);
  border-radius: 3px;
  cursor: pointer;
  position: relative;
  min-width: 80px;
}
.player__progress-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: linear-gradient(90deg, rgba(168, 197, 232, 0.8), rgba(232, 184, 168, 0.6));
  border-radius: 3px;
  transition: width 0.15s linear;
}
.player__volume {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.player__volume-icon {
  font-size: 14px;
}
.player__volume-slider {
  width: 70px;
  accent-color: rgba(168, 197, 232, 0.9);
}

/* toast */
.toast {
  position: fixed;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(90, 70, 50, 0.9);
  color: #fff;
  padding: 10px 22px;
  border-radius: 20px;
  font-size: 14px;
  z-index: 100;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(6px);
  white-space: nowrap;
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
  .western-header {
    padding: calc(20px + env(safe-area-inset-top)) 18px 26px;
  }
  .western-header__inner {
    gap: 14px;
  }
  .western-header__glyph {
    font-size: 48px;
  }
  .western-header__title {
    font-size: 22px;
  }
  .visualizer-wrap,
  .groups {
    padding: 0 14px;
  }
  .groups {
    margin-top: 20px;
  }
  .track-item {
    padding: 12px 14px;
    gap: 12px;
  }
  /* 播放器上移避开 tabbar */
  .player {
    bottom: calc(72px + env(safe-area-inset-bottom));
  }
  .player__inner {
    flex-wrap: wrap;
    padding: 10px 14px;
    gap: 10px;
  }
  .player__info {
    flex: 1 1 100%;
    max-width: none;
    min-width: 0;
  }
  .player__controls {
    order: 2;
    margin: 0 auto;
  }
  .player__progress {
    flex: 1 1 100%;
    order: 3;
  }
  .player__volume {
    display: none;
  }
  .western-view {
    padding-bottom: calc(220px + env(safe-area-inset-bottom));
  }
  .toast {
    bottom: calc(190px + env(safe-area-inset-bottom));
  }
}

/* 平板：播放器正常贴底 */
@media (min-width: 769px) and (max-width: 1024px) {
  .player {
    bottom: 0;
  }
}
</style>
