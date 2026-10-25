<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const problem = ref('')
const selectedTags = ref([])
const loading = ref(false)
const result = ref(null)
const errorMsg = ref('')

const baduanjinDone = ref(false)
const checking = ref(false)
const interests = ref({})

const audioEl = ref(null)
const rewardClaimed = ref(false)
const toast = ref('')
let toastTimer = null

const quickTags = [
  { key: 'sleep', label: '睡不着' },
  { key: 'anxiety', label: '焦虑' },
  { key: 'fatigue', label: '疲惫' },
  { key: 'digestion', label: '脾胃不舒服' },
  { key: 'low_mood', label: '低落' },
  { key: 'irritability', label: '烦躁' },
]

const toggleTag = (key) => {
  selectedTags.value = selectedTags.value.includes(key)
    ? selectedTags.value.filter(k => k !== key)
    : [...selectedTags.value, key]
}

const showToast = (text, duration = 2400) => {
  toast.value = text
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, duration)
}

const submit = async () => {
  if (!problem.value.trim() && selectedTags.value.length === 0) {
    errorMsg.value = '先说说此刻哪里不舒服，或选一个状态标签'
    return
  }
  loading.value = true
  errorMsg.value = ''
  result.value = null
  rewardClaimed.value = false
  try {
    const res = await api.post('/therapy/recommend', {
      problem: problem.value.trim() || selectedTags.value.join(' '),
      tags: selectedTags.value,
    })
    result.value = res
    baduanjinDone.value = false
    fetchBaduanjinStatus()
  } catch (e) {
    errorMsg.value = e.message || '推荐失败，请稍后再试'
  } finally {
    loading.value = false
  }
}

const fetchBaduanjinStatus = async () => {
  if (!userStore.isLoggedIn) return
  try {
    const res = await api.get('/therapy/baduanjin/status')
    baduanjinDone.value = !!res?.checked_in
  } catch {
    // 静默
  }
}

const playMusic = () => {
  if (!audioEl.value) return
  rewardClaimed.value = false
  audioEl.value.currentTime = 0
  audioEl.value.play()
}

const onTimeUpdate = async () => {
  const el = audioEl.value
  if (!el || rewardClaimed.value) return
  if (!el.duration || el.currentTime / el.duration < 0.9) return
  rewardClaimed.value = true
  if (!userStore.isLoggedIn) {
    showToast('登录后听完曲子可获得 1 露水')
    return
  }
  try {
    const track = result.value?.music?.track
    if (!track?.id) return
    const res = await api.post('/music/listen-complete', {
      music_id: track.id,
      progress: 0.95,
    })
    if (res?.granted && typeof res.new_total_energy === 'number') {
      userStore.updateEnergy(res.new_total_energy)
      if (typeof res.leaves_balance === 'number') {
        userStore.updateResources({ leaves: res.leaves_balance })
      }
      showToast('听完一曲，+1 露水 🌿')
    } else if (res?.reason) {
      showToast(res.reason)
    }
  } catch (e) {
    rewardClaimed.value = false
    showToast(e.message || '露水发放失败')
  }
}

const checkinBaduanjin = async () => {
  if (!userStore.isLoggedIn) {
    router.push({ name: 'login', query: { next: '/music/therapy' } })
    return
  }
  if (baduanjinDone.value || checking.value) return
  checking.value = true
  try {
    const res = await api.post('/therapy/baduanjin/checkin', { move_key: 'general' })
    baduanjinDone.value = true
    if (typeof res?.new_total_energy === 'number') {
      userStore.updateEnergy(res.new_total_energy)
    }
    showToast('今日跟练打卡完成，+1 露水 🌿')
  } catch (e) {
    showToast(e.message || '打卡失败')
  } finally {
    checking.value = false
  }
}

const reserve = async (product) => {
  if (product.purchase_url) {
    window.open(product.purchase_url, '_blank', 'noopener')
    return
  }
  if (!userStore.isLoggedIn) {
    router.push({ name: 'login', query: { next: '/music/therapy' } })
    return
  }
  try {
    await api.post('/therapy/interest', { product_key: product.key })
    interests.value[product.key] = true
    showToast('已记下你的预约意向，上架后会优先通知你')
  } catch (e) {
    showToast(e.message || '预约失败')
  }
}

const hasResult = computed(() => !!result.value)

onMounted(() => {
  fetchBaduanjinStatus()
})

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
  if (audioEl.value) audioEl.value.pause()
})
</script>

<template>
  <div class="therapy-view">
    <header class="therapy-header">
      <button class="back-btn" @click="router.push('/music')">← 回琴音疗心</button>
      <h1 class="therapy-title">🌿 身心调理</h1>
      <p class="therapy-verse">"说说你此刻的状态，静屿为你配一曲、一式、一枚香囊、一份温和的吃食"</p>
    </header>

    <section class="therapy-form card">
      <label class="form-label">此刻的你，哪里不太舒服？</label>
      <textarea
        v-model="problem"
        class="form-textarea"
        rows="4"
        placeholder="例如：最近总是睡不着，心里很紧；或者饭后肚子胀、没什么胃口…"
      ></textarea>
      <div class="quick-tags">
        <button
          v-for="tag in quickTags"
          :key="tag.key"
          class="quick-tag"
          :class="{ 'is-active': selectedTags.includes(tag.key) }"
          @click="toggleTag(tag.key)"
        >{{ tag.label }}</button>
      </div>
      <div class="form-actions">
        <button class="btn btn--primary" :disabled="loading" @click="submit">
          {{ loading ? '正在为你配…' : '开始调理' }}
        </button>
        <span class="form-hint">不诊断、不开药，只给传统养生与生活方式参考</span>
      </div>
      <p v-if="errorMsg" class="form-error">{{ errorMsg }}</p>
    </section>

    <template v-if="hasResult">
      <section class="result-block">
        <div class="result-label">当前方向：{{ result.category.label }}</div>

        <!-- 1. 古琴曲 -->
        <div class="result-card card music-card">
          <div class="result-card__head">
            <span class="result-card__icon">🎵</span>
            <div>
              <h2 class="result-card__title">先听一曲</h2>
              <p class="result-card__sub">{{ result.music.reason }}</p>
            </div>
          </div>
          <div v-if="result.music.track" class="track">
            <div class="track__meta">
              <div class="track__title">{{ result.music.track.title }}</div>
              <div class="track__sub">{{ result.music.yin_type }} 音 · {{ Math.round(result.music.track.duration || 0) }} 秒</div>
            </div>
            <audio
              ref="audioEl"
              :src="result.music.track.audio_url"
              preload="metadata"
              controls
              @timeupdate="onTimeUpdate"
            ></audio>
            <button class="btn btn--ghost track__play" @click="playMusic">▶ 播放</button>
          </div>
          <p class="result-card__hint">听完 90% 可获 1 露水（同曲 24 小时内不重复，每日上限 20）。</p>
        </div>

        <!-- 2. 八段锦 -->
        <div class="result-card card">
          <div class="result-card__head">
            <span class="result-card__icon">🧘</span>
            <div>
              <h2 class="result-card__title">配一式八段锦</h2>
              <p class="result-card__sub">动作缓慢、配合呼吸，不舒服就停。</p>
            </div>
          </div>

          <!-- 八段锦跟练视频（Bilibili 嵌入） -->
          <div class="video-frame">
            <iframe
              src="https://player.bilibili.com/player.html?isOutside=true&aid=46964958&bvid=BV1Nb41177h8&cid=82258764&p=1"
              title="八段锦跟练视频"
              scrolling="no"
              frameborder="0"
              allowfullscreen="true"
              allow="autoplay; fullscreen"
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
            ></iframe>
          </div>
          <p class="video-hint">
            视频来自 Bilibili · <a href="https://www.bilibili.com/video/BV1Nb41177h8" target="_blank" rel="noopener">在 B 站打开</a>
          </p>

          <div class="moves">
            <div v-for="move in result.baduanjin" :key="move.key" class="move">
              <div class="move__name">{{ move.name }}</div>
              <div class="move__focus">{{ move.focus }}</div>
              <ol class="move__steps">
                <li v-for="(step, i) in move.steps" :key="i">{{ step }}</li>
              </ol>
              <a class="move__link" :href="move.video_url" target="_blank" rel="noopener">看视频演示 →</a>
            </div>
          </div>
          <div class="checkin-row">
            <button class="btn btn--primary" :disabled="baduanjinDone || checking" @click="checkinBaduanjin">
              {{ baduanjinDone ? '今日已跟练 ✅' : (checking ? '打卡中…' : '今日跟练打卡 +1 露水') }}
            </button>
            <span class="checkin-hint">每天一次；登录后计入露水。</span>
          </div>
        </div>

        <!-- 3. 香囊 / 手串 / 食疗 -->
        <div class="result-card card">
          <div class="result-card__head">
            <span class="result-card__icon">🎁</span>
            <div>
              <h2 class="result-card__title">岛上好物</h2>
              <p class="result-card__sub">可选，不买也完全不影响调理；当前为橱窗展示与预约，暂未开通支付。</p>
            </div>
          </div>
          <div class="products">
            <div v-for="product in [result.sachet, result.bracelet, result.food]" :key="product.key" class="product">
              <div class="product__type">{{ product.type === 'sachet' ? '香囊' : product.type === 'bracelet' ? '手串' : '食疗' }}</div>
              <div class="product__name">{{ product.name }}</div>
              <div class="product__price">¥{{ product.price.toFixed(1) }}</div>
              <p class="product__note">{{ product.note }}</p>
              <p v-if="product.allergens" class="product__allergen">过敏原 / 注意：{{ product.allergens }}</p>
              <p v-else-if="product.material" class="product__allergen">材质：{{ product.material }}</p>
              <p v-else-if="product.ingredients" class="product__allergen">成分：{{ product.ingredients }}</p>
              <button class="btn btn--ghost product__btn" @click="reserve(product)">
                {{ product.purchase_url ? '去购买' : (interests[product.key] ? '已预约 ✅' : '预约 / 了解') }}
              </button>
            </div>
          </div>
        </div>

        <p class="disclaimer">{{ result.disclaimer }}</p>
      </section>
    </template>

    <transition name="toast">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </transition>
  </div>
</template>

<style scoped>
.therapy-view {
  max-width: 980px;
  margin: 0 auto;
  padding: 32px 24px 90px;
}
.back-btn {
  background: none;
  border: none;
  color: #8B7B5E;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0;
}
.therapy-header {
  text-align: center;
  margin-bottom: 24px;
}
.therapy-title {
  font-size: 1.9rem;
  color: #5C5348;
  margin: 16px 0 8px;
}
.therapy-verse {
  color: #9A8F7E;
  font-size: 0.9rem;
  line-height: 1.7;
}
.therapy-form {
  padding: 22px 24px;
}
.form-label {
  display: block;
  font-size: 0.9rem;
  color: #5C5348;
  margin-bottom: 10px;
}
.form-textarea {
  width: 100%;
  border: 1px solid #E6DCCD;
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 0.92rem;
  line-height: 1.7;
  color: #5C5348;
  background: #FFFDF8;
  resize: vertical;
  outline: none;
  font-family: inherit;
}
.quick-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.quick-tag {
  border: 1px solid #E6DCCD;
  background: #FFFDF8;
  color: #8B7B5E;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 0.82rem;
  cursor: pointer;
}
.quick-tag.is-active {
  background: #E8D5A8;
  border-color: #D4B88A;
  color: #5C5348;
}
.form-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.form-hint {
  font-size: 0.78rem;
  color: #A89C8B;
}
.form-error {
  color: #C97B7B;
  font-size: 0.84rem;
  margin: 10px 0 0;
}
.result-block {
  margin-top: 24px;
  display: grid;
  gap: 18px;
}
.result-label {
  font-size: 0.85rem;
  color: #8B7B5E;
  padding-left: 4px;
}
.result-card {
  padding: 22px 24px;
}
.result-card__head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 14px;
}
.result-card__icon {
  font-size: 1.4rem;
}
.result-card__title {
  font-size: 1.05rem;
  color: #5C5348;
  margin: 0 0 4px;
}
.result-card__sub {
  font-size: 0.82rem;
  color: #9A8F7E;
  line-height: 1.6;
  margin: 0;
}
.track {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  background: #FBF7EF;
  border-radius: 14px;
  padding: 14px 16px;
}
.track__meta {
  min-width: 130px;
}
.track__title {
  color: #5C5348;
  font-weight: 600;
}
.track__sub {
  font-size: 0.78rem;
  color: #A89C8B;
  margin-top: 2px;
}
.track audio {
  flex: 1;
  min-width: 220px;
  height: 36px;
}
.track__play {
  flex-shrink: 0;
}
.result-card__hint {
  font-size: 0.78rem;
  color: #A89C8B;
  margin: 10px 0 0;
}
.moves {
  display: grid;
  gap: 14px;
}
.video-frame {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  border-radius: 14px;
  overflow: hidden;
  background: #000;
  margin: 4px 0 10px;
}
.video-frame iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.video-hint {
  font-size: 0.76rem;
  color: #A89C8B;
  margin: 0 0 14px;
}
.video-hint a {
  color: #8FAE88;
  text-decoration: none;
}
.move {
  background: #FBF7EF;
  border-radius: 14px;
  padding: 14px 16px;
}
.move__name {
  color: #5C5348;
  font-weight: 600;
}
.move__focus {
  font-size: 0.8rem;
  color: #8B7B5E;
  margin: 3px 0 8px;
}
.move__steps {
  margin: 0 0 8px;
  padding-left: 20px;
  color: #6B6053;
  font-size: 0.85rem;
  line-height: 1.7;
}
.move__link {
  font-size: 0.8rem;
  color: #8FAE88;
  text-decoration: none;
}
.checkin-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.checkin-hint {
  font-size: 0.78rem;
  color: #A89C8B;
}
.products {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.product {
  position: relative;
  background: #FBF7EF;
  border-radius: 16px;
  padding: 16px;
}
.product__type {
  font-size: 0.72rem;
  color: #A89C8B;
}
.product__name {
  color: #5C5348;
  font-weight: 600;
  margin: 4px 0 2px;
}
.product__price {
  color: #8B7B5E;
  font-size: 0.88rem;
}
.product__note {
  font-size: 0.78rem;
  color: #8B7B5E;
  line-height: 1.6;
  margin: 8px 0;
}
.product__allergen {
  font-size: 0.72rem;
  color: #B58A6A;
  line-height: 1.5;
  margin: 0 0 8px;
}
.product__btn {
  font-size: 0.78rem;
  padding: 6px 12px;
}
.disclaimer {
  font-size: 0.76rem;
  color: #A89C8B;
  line-height: 1.7;
  background: #FBF7EF;
  border-radius: 12px;
  padding: 14px 16px;
  margin: 0;
}
@media (max-width: 768px) {
  .products {
    grid-template-columns: 1fr;
  }
  .track audio {
    min-width: 100%;
  }
}
</style>
