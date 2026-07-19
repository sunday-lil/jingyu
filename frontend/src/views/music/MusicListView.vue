<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'

const router = useRouter()

// 五音常量（前端写死）
const YIN_INFO = {
  gong: { name: '宫', element: '土', organ: '脾', color: '#E8B8A8', description: '安神厚德，如大地承载' },
  shang: { name: '商', element: '金', organ: '肺', color: '#E8C5A8', description: '肃降清心，如秋露澄澈' },
  jue: { name: '角', element: '木', organ: '肝', color: '#A8C5A0', description: '疏达生发，如春风化雨' },
  zhi: { name: '徵', element: '火', organ: '心', color: '#E8A8B8', description: '温养喜悦，如夏阳和煦' },
  yu: { name: '羽', element: '水', organ: '肾', color: '#A8B8C5', description: '润下守静，如冬潭深沉' },
}

// 转为数组便于渲染
const yinList = Object.entries(YIN_INFO).map(([key, info]) => ({ key, ...info }))

// AI 推荐相关
const userInput = ref('')
const loading = ref(false)

// 跳转到详情页
const goToDetail = (key) => {
  router.push(`/music/${key}`)
}

// AI 推荐选音
const recommendMusic = async () => {
  const text = userInput.value.trim()
  if (!text) {
    alert('请描述一下你现在的状态～')
    return
  }
  loading.value = true
  try {
    const res = await api.post('/ai/recommend-music', { user_state: text })
    const { yin, reason, available } = res.data || {}
    if (!available || !YIN_INFO[yin]) {
      alert('暂时无法为你推荐，请稍后再试')
      return
    }
    alert(`AI 为你推荐：${YIN_INFO[yin].name}音\n${reason || ''}`)
    router.push(`/music/${yin}`)
  } catch (e) {
    alert('推荐失败，请稍后再试')
  } finally {
    loading.value = false
  }
}

// 入场动画：卡片 stagger 浮入
onMounted(() => {
  nextTick(() => {
    gsap.from('.ai-section', {
      y: -20,
      opacity: 0,
      duration: 0.6,
      ease: 'power2.out',
    })
    gsap.from('.yin-card', {
      y: 30,
      opacity: 0,
      duration: 0.8,
      stagger: 0.12,
      ease: 'power3.out',
    })
  })
})
</script>

<template>
  <div class="music-list-view">
    <!-- AI 帮我选音入口 -->
    <section class="ai-section">
      <div class="ai-section__inner">
        <h2 class="ai-section__title">AI 帮我选音</h2>
        <p class="ai-section__subtitle">描述一下你此刻的状态，让 AI 为你择一音疗愈</p>
        <div class="ai-section__input-row">
          <input
            v-model="userInput"
            class="ai-section__input"
            type="text"
            placeholder="例如：焦虑睡不着 / 心烦气躁 / 疲惫乏力"
            @keyup.enter="recommendMusic"
          />
          <button
            class="ai-section__btn"
            :disabled="loading"
            @click="recommendMusic"
          >
            {{ loading ? '推荐中…' : '为我选音' }}
          </button>
        </div>
      </div>
    </section>

    <!-- 五音卡片 -->
    <section class="yin-grid">
      <div
        v-for="item in yinList"
        :key="item.key"
        class="yin-card"
        :style="{ '--card-color': item.color }"
        @click="goToDetail(item.key)"
      >
        <div class="yin-card__glyph">{{ item.name }}</div>
        <div class="yin-card__meta">
          <span class="yin-card__element">{{ item.element }}</span>
          <span class="yin-card__divider">·</span>
          <span class="yin-card__organ">入{{ item.organ }}</span>
        </div>
        <p class="yin-card__desc">{{ item.description }}</p>
        <div class="yin-card__enter">进入 →</div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.music-list-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* AI 推荐区 */
.ai-section {
  margin-bottom: 48px;
}
.ai-section__inner {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 8px 32px rgba(180, 160, 140, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.5);
}
.ai-section__title {
  font-family: var(--font-serif, serif);
  font-size: 22px;
  color: var(--color-text-primary, #5a4a3a);
  margin: 0 0 6px;
  font-weight: 500;
}
.ai-section__subtitle {
  font-size: 13px;
  color: var(--color-text-secondary, #8a7a6a);
  margin: 0 0 18px;
}
.ai-section__input-row {
  display: flex;
  gap: 10px;
}
.ai-section__input {
  flex: 1;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(200, 180, 160, 0.3);
  border-radius: 14px;
  padding: 12px 16px;
  font-size: 14px;
  color: var(--color-text-primary, #5a4a3a);
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}
.ai-section__input::placeholder {
  color: rgba(138, 122, 106, 0.6);
}
.ai-section__input:focus {
  border-color: rgba(180, 160, 140, 0.6);
}
.ai-section__btn {
  background: linear-gradient(135deg, #d4b8a0, #c5a890);
  color: #fff;
  border: none;
  border-radius: 14px;
  padding: 0 22px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
  font-family: inherit;
  white-space: nowrap;
}
.ai-section__btn:hover:not(:disabled) {
  transform: translateY(-1px);
}
.ai-section__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 五音网格：桌面 5 列，移动 2 列 */
.yin-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
}
@media (max-width: 768px) {
  .yin-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
  }
}

.yin-card {
  position: relative;
  background: linear-gradient(160deg, var(--card-color), rgba(255, 255, 255, 0.65));
  border-radius: 28px;
  padding: 28px 20px;
  cursor: pointer;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(150, 130, 110, 0.15);
  transition: transform 0.35s ease, box-shadow 0.35s ease;
  border: 1px solid rgba(255, 255, 255, 0.4);
}
.yin-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.5), transparent 60%);
  pointer-events: none;
}
.yin-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 40px rgba(150, 130, 110, 0.22);
}
.yin-card__glyph {
  font-family: var(--font-serif, serif);
  font-size: 56px;
  color: rgba(90, 70, 50, 0.85);
  line-height: 1;
  margin-bottom: 16px;
  font-weight: 500;
  position: relative;
}
.yin-card__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(90, 70, 50, 0.7);
  margin-bottom: 12px;
  position: relative;
}
.yin-card__divider {
  opacity: 0.5;
}
.yin-card__desc {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(90, 70, 50, 0.75);
  margin: 0 0 18px;
  min-height: 42px;
  position: relative;
}
.yin-card__enter {
  font-size: 12px;
  color: rgba(90, 70, 50, 0.6);
  letter-spacing: 1px;
  position: relative;
}
@media (max-width: 768px) {
  .yin-card__glyph {
    font-size: 44px;
  }
  .yin-card {
    padding: 22px 16px;
  }
  .music-list-view {
    padding: 20px 16px 60px;
  }
  .ai-section__inner {
    padding: 22px;
  }
  .ai-section__title {
    font-size: 18px;
  }
  .ai-section__input-row {
    flex-direction: column;
  }
  .ai-section__btn {
    padding: 12px;
  }
}
</style>
