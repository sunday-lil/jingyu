<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'

// 路由通过 props: true 注入 yin 参数
const props = defineProps({
  yin: { type: String, required: true },
})

// 五音常量（前端写死）
const YIN_INFO = {
  gong: { name: '宫', element: '土', organ: '脾', color: '#E8B8A8', description: '安神厚德，如大地承载' },
  shang: { name: '商', element: '金', organ: '肺', color: '#E8C5A8', description: '肃降清心，如秋露澄澈' },
  jue: { name: '角', element: '木', organ: '肝', color: '#A8C5A0', description: '疏达生发，如春风化雨' },
  zhi: { name: '徵', element: '火', organ: '心', color: '#E8A8B8', description: '温养喜悦，如夏阳和煦' },
  yu: { name: '羽', element: '水', organ: '肾', color: '#A8B8C5', description: '润下守静，如冬潭深沉' },
}

const route = useRoute()

// 当前音 key（优先取 props，回退到路由参数）
const yinKey = computed(() => props.yin || route.params.yin)
const yinInfo = computed(() => YIN_INFO[yinKey.value] || YIN_INFO.gong)

// 数据
const musics = ref([])
const loading = ref(false)
const errorMsg = ref('')

// 播放器状态
const audioEl = ref(null)
const currentIndex = ref(-1)
const currentMusic = computed(() =>
  currentIndex.value >= 0 ? musics.value[currentIndex.value] : null
)
const isPlaying = ref(false)
const progress = ref(0) // 0-1
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.8)
const listenReported = ref(false) // 当前曲目是否已上报聆听完成

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
  }, 2000)
}

// 时间格式化
const formatTime = (sec) => {
  if (!sec || isNaN(sec)) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
const formatDuration = (d) => (d ? formatTime(d) : '--:--')

// 拉取该音的曲目列表
const fetchMusics = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get(`/music/yin/${yinKey.value}`)
    musics.value = res.data?.musics || []
  } catch (e) {
    errorMsg.value = '曲目加载失败，请稍后再试'
  } finally {
    loading.value = false
  }
}

// 选中并播放
const playIndex = (idx) => {
  if (idx < 0 || idx >= musics.value.length) return
  currentIndex.value = idx
  listenReported.value = false
  const audio = audioEl.value
  if (!audio) return
  audio.load()
  audio.volume = volume.value
  audio
    .play()
    .then(() => {
      isPlaying.value = true
    })
    .catch(() => {
      // 自动播放被拦截
      isPlaying.value = false
    })
}

// 播放/暂停切换
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

// 上一首 / 下一首（循环）
const playPrev = () => {
  if (musics.value.length === 0) return
  const idx =
    currentIndex.value <= 0 ? musics.value.length - 1 : currentIndex.value - 1
  playIndex(idx)
}
const playNext = () => {
  if (musics.value.length === 0) return
  const idx = (currentIndex.value + 1) % musics.value.length
  playIndex(idx)
}

// 播放进度更新
const onTimeUpdate = () => {
  const audio = audioEl.value
  if (!audio) return
  currentTime.value = audio.currentTime
  duration.value = audio.duration || 0
  if (duration.value > 0) {
    progress.value = audio.currentTime / audio.duration
    // 听完 90% 上报聆听完成
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

// 进度条点击跳转
const seek = (e) => {
  const audio = audioEl.value
  if (!audio || !audio.duration) return
  const rect = e.currentTarget.getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  audio.currentTime = ratio * audio.duration
  progress.value = ratio
}

// 音量调节
const onVolumeChange = (e) => {
  volume.value = parseFloat(e.target.value)
  if (audioEl.value) {
    audioEl.value.volume = volume.value
  }
}

// 上报聆听完成
const reportListenComplete = async () => {
  if (!currentMusic.value) return
  listenReported.value = true
  try {
    const res = await api.post('/music/listen-complete', {
      music_id: currentMusic.value.id,
      progress: Math.round(progress.value * 100),
    })
    if (res.data?.granted) {
      showToast('+1 露水 💧')
    }
  } catch (e) {
    // 静默失败，不影响聆听体验
  }
}

// 停止播放并重置
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

// yin 变化时重新加载
watch(yinKey, () => {
  stopAudio()
  fetchMusics()
})

onMounted(() => {
  fetchMusics()
  nextTick(() => {
    if (audioEl.value) audioEl.value.volume = volume.value
  })
})

onBeforeUnmount(() => {
  stopAudio()
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="music-detail-view" :style="{ '--accent': yinInfo.color }">
    <!-- 顶部信息 -->
    <header class="detail-header">
      <div class="detail-header__inner">
        <div class="detail-header__glyph">{{ yinInfo.name }}</div>
        <div class="detail-header__text">
          <h1 class="detail-header__title">{{ yinInfo.name }}音 · 入{{ yinInfo.organ }}</h1>
          <p class="detail-header__desc">{{ yinInfo.description }}</p>
          <div class="detail-header__meta">
            <span>{{ yinInfo.element }}行</span>
            <span class="dot">·</span>
            <span>共 {{ musics.length }} 首疗愈曲</span>
          </div>
        </div>
      </div>
    </header>

    <!-- 曲目列表 -->
    <section class="track-list">
      <div v-if="loading" class="track-list__empty">曲目加载中…</div>
      <div v-else-if="errorMsg" class="track-list__empty">{{ errorMsg }}</div>
      <div v-else-if="musics.length === 0" class="track-list__empty">暂无曲目</div>
      <ul v-else class="track-list__ul">
        <li
          v-for="(m, idx) in musics"
          :key="m.id"
          class="track-item"
          :class="{ 'is-active': idx === currentIndex }"
          @click="playIndex(idx)"
        >
          <div class="track-item__index">
            <span v-if="idx === currentIndex && isPlaying">♪</span>
            <span v-else>{{ String(idx + 1).padStart(2, '0') }}</span>
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
    </section>

    <!-- 底部固定播放器 -->
    <footer v-if="currentMusic" class="player">
      <div class="player__inner">
        <div class="player__info">
          <div class="player__title">{{ currentMusic.title }}</div>
          <div class="player__sub">
            {{ yinInfo.name }}音 · {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
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

    <!-- 原生 audio 元素 -->
    <audio
      ref="audioEl"
      :src="currentMusic?.audio_url || ''"
      @timeupdate="onTimeUpdate"
      @ended="onEnded"
      @play="isPlaying = true"
      @pause="isPlaying = false"
    ></audio>

    <!-- toast 轻提示 -->
    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.music-detail-view {
  min-height: 100vh;
  padding-bottom: 140px;
}

/* 顶部信息区 */
.detail-header {
  background: linear-gradient(160deg, var(--accent), rgba(255, 255, 255, 0.7));
  padding: 40px 24px 48px;
  border-bottom-left-radius: 32px;
  border-bottom-right-radius: 32px;
  box-shadow: 0 10px 30px rgba(150, 130, 110, 0.12);
}
.detail-header__inner {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 28px;
}
.detail-header__glyph {
  font-family: var(--font-serif, serif);
  font-size: 72px;
  color: rgba(90, 70, 50, 0.85);
  font-weight: 500;
  line-height: 1;
  flex-shrink: 0;
}
.detail-header__title {
  font-family: var(--font-serif, serif);
  font-size: 26px;
  color: rgba(90, 70, 50, 0.9);
  margin: 0 0 8px;
  font-weight: 500;
}
.detail-header__desc {
  font-size: 14px;
  color: rgba(90, 70, 50, 0.75);
  margin: 0 0 10px;
  line-height: 1.6;
}
.detail-header__meta {
  font-size: 12px;
  color: rgba(90, 70, 50, 0.6);
  display: flex;
  gap: 6px;
  align-items: center;
}
.detail-header__meta .dot {
  opacity: 0.5;
}
@media (max-width: 640px) {
  .detail-header {
    padding: 28px 20px 32px;
  }
  .detail-header__inner {
    gap: 18px;
  }
  .detail-header__glyph {
    font-size: 52px;
  }
  .detail-header__title {
    font-size: 20px;
  }
}

/* 曲目列表 */
.track-list {
  max-width: 1000px;
  margin: 32px auto 0;
  padding: 0 24px;
}
.track-list__empty {
  text-align: center;
  color: var(--color-text-secondary, #8a7a6a);
  padding: 60px 0;
  font-size: 14px;
}
.track-list__ul {
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
  background: linear-gradient(135deg, var(--accent), rgba(255, 255, 255, 0.6));
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

/* 底部固定播放器 */
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
  background: linear-gradient(135deg, var(--accent), rgba(255, 255, 255, 0.6));
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
  background: linear-gradient(90deg, var(--accent), rgba(255, 255, 255, 0.5));
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
  accent-color: var(--accent);
}

/* 移动端播放器适配 */
@media (max-width: 768px) {
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
  .track-list {
    padding: 0 16px;
    margin-top: 22px;
  }
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
</style>
