<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'

const router = useRouter()
const route = useRoute()
const notes = ref([])
const loading = ref(true)
const errorMsg = ref('')
const toastVisible = ref(false)
const toastText = ref('')
let toastTimer = null

const showToast = (text) => {
  toastText.value = text
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2600)
}

const formatDate = (str) => {
  if (!str) return ''
  const d = new Date(str)
  if (isNaN(d.getTime())) return str
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const orbStyle = (i) => ({
  left: `${20 + ((i * 13) % 58)}%`,
  animationDelay: `${i * 0.35}s`,
  fontSize: `${18 + (i % 3) * 3}px`,
})

const playBuriedAnimation = () => new Promise((resolve) => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    showToast('胶囊已埋进树下 🌳')
    resolve()
    return
  }
  const tl = gsap.timeline({ onComplete: resolve })
  tl.set('.capsule-falling', { opacity: 1, y: -150, scale: 1, rotate: -8 })
    .to('.capsule-falling', { y: 0, rotate: 0, duration: 1.25, ease: 'bounce.out' })
    .to('.tree__canopy', { scale: 1.06, duration: 0.35, yoyo: true, repeat: 1, ease: 'sine.inOut' }, '-=0.35')
    .to('.capsule-falling', { opacity: 0, scale: 0.5, y: 18, duration: 0.45 }, '+=0.15')
    .call(() => showToast('胶囊已埋进树下 🌳'))
})

const fetchNotes = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get('/diary/capsule')
    notes.value = res?.items || []
    await nextTick()
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      loading.value = false
      return
    }
    gsap.from('.tree-scene', { y: 24, duration: 0.9, ease: 'power3.out', clearProps: 'transform' })
    if (document.querySelector('.capsule-note')) {
      gsap.from('.capsule-note', {
        y: 20, duration: 0.6, stagger: 0.07, ease: 'power3.out', clearProps: 'transform',
      })
    }
    if (route.query.buried === '1') {
      // 内容先显示，埋胶囊动画在后台播放，不让页面停留在 loading
      playBuriedAnimation().then(() => router.replace('/diary/capsule'))
    }
  } catch (e) {
    errorMsg.value = e.message || '胶囊加载失败'
  } finally {
    loading.value = false
  }
}

const goWrite = () => router.push('/diary/write?mode=capsule')

const removeNote = async (id) => {
  if (!confirm('确定要取出这颗时光胶囊吗？取出后不可恢复。')) return
  try {
    await api.delete(`/diary/${id}`)
    notes.value = notes.value.filter(n => n.id !== id)
    showToast('胶囊已取出')
  } catch (e) {
    alert(e.message || '取出失败')
  }
}

onMounted(fetchNotes)
onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
  gsap.killTweensOf(['.tree-scene', '.capsule-note', '.capsule-falling', '.tree__canopy'])
})
</script>

<template>
  <div class="capsule-view">
    <header class="capsule-header">
      <button class="back-btn" @click="router.push('/diary')">← 回日记海岸</button>
      <h1 class="capsule-title">🌳 时光胶囊</h1>
      <p class="capsule-verse">"不想漂走的日记，埋在树下，等时间替你保管。"</p>
      <button class="btn btn--primary" @click="goWrite">✍️ 写一颗胶囊</button>
    </header>

    <!-- 树下埋胶囊的插画场景 -->
    <section class="tree-scene" aria-hidden="true">
      <div class="tree-scene__sky"></div>
      <div class="tree-scene__stars">
        <span v-for="i in 8" :key="i" :style="{ left: `${8 + i * 10}%`, top: `${12 + (i % 4) * 13}%` }"></span>
      </div>
      <div class="tree">
        <div class="tree__canopy tree__canopy--left"></div>
        <div class="tree__canopy tree__canopy--right"></div>
        <div class="tree__canopy tree__canopy--top"></div>
        <div class="tree__trunk"></div>
        <div class="tree__branch tree__branch--left"></div>
        <div class="tree__branch tree__branch--right"></div>
        <div class="tree__roots"></div>
        <div class="capsule-falling">🫙</div>
        <div class="capsule-orbs">
          <span
            v-for="(note, i) in notes.slice(0, 9)"
            :key="note.id"
            class="capsule-orb"
            :style="orbStyle(i)"
          >🫙</span>
        </div>
      </div>
      <div class="tree-scene__ground"></div>
      <p class="tree-scene__hint">
        {{ notes.length ? `树下已经埋了 ${notes.length} 颗胶囊` : '树下还没有胶囊' }}
      </p>
    </section>

    <section class="capsule-list">
      <div v-if="loading" class="capsule-state">正在拨开树根旁的土…</div>
      <div v-else-if="errorMsg" class="capsule-state">{{ errorMsg }}</div>
      <div v-else-if="notes.length === 0" class="capsule-state">
        <div class="capsule-state__emoji">🌱</div>
        <p>这里还没有胶囊。写一段不想被海风吹走的话，把它埋在树下。</p>
        <button class="btn btn--primary" @click="goWrite">写第一颗胶囊</button>
      </div>
      <div v-else class="capsule-notes">
        <article v-for="note in notes" :key="note.id" class="capsule-note card">
          <div class="capsule-note__head">
            <span class="capsule-note__date">🌳 {{ formatDate(note.created_at) }}</span>
            <button class="capsule-note__delete" @click="removeNote(note.id)">取出</button>
          </div>
          <p class="capsule-note__content">{{ note.content }}</p>
        </article>
      </div>
    </section>

    <transition name="toast">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style scoped>
.capsule-view {
  position: relative;
  max-width: 820px;
  margin: 0 auto;
  padding: 28px 24px 90px;
}
.capsule-header { text-align: center; margin-bottom: 20px; }
.back-btn {
  position: absolute; left: 24px; top: 28px;
  background: none; border: none; color: #8B7B5E;
  cursor: pointer; font-size: 0.9rem;
}
.capsule-title { font-size: 1.9rem; color: #5C5348; margin: 18px 0 8px; }
.capsule-verse { color: #9A8F7E; font-size: 0.9rem; margin-bottom: 18px; }

.tree-scene {
  position: relative;
  height: 320px;
  margin: 8px 0 28px;
  border-radius: 28px;
  overflow: hidden;
  background: linear-gradient(180deg, #F7F1E5 0%, #E8F0E5 58%, #D8E4D2 100%);
  border: 1px solid rgba(255,255,255,.7);
  box-shadow: 0 12px 36px rgba(139,123,94,.12);
}
.tree-scene__sky {
  position: absolute; inset: 0;
  background: radial-gradient(circle at 72% 18%, rgba(255,244,210,.9), transparent 32%);
}
.tree-scene__stars span {
  position: absolute; width: 3px; height: 3px; border-radius: 50%;
  background: rgba(255,255,255,.9); box-shadow: 0 0 8px #fff;
}
.tree {
  position: absolute; left: 50%; bottom: 30px;
  width: 260px; height: 250px; transform: translateX(-50%);
  transform-origin: 50% 100%;
}
.tree__trunk {
  position: absolute; left: 50%; bottom: 20px;
  width: 22px; height: 125px; margin-left: -11px;
  border-radius: 12px 12px 4px 4px;
  background: linear-gradient(90deg, #8B654A, #B08968 55%, #7A563E);
  z-index: 2;
}
.tree__branch {
  position: absolute; height: 9px; border-radius: 9px;
  background: #8B654A; z-index: 1;
}
.tree__branch--left { left: 50%; bottom: 120px; width: 78px; transform: rotate(24deg); transform-origin: left center; }
.tree__branch--right { right: 50%; bottom: 138px; width: 70px; transform: rotate(-28deg); transform-origin: right center; }
.tree__canopy {
  position: absolute; border-radius: 50%; z-index: 3;
  background: radial-gradient(circle at 35% 30%, #C5DFC0, #8FBE8A 62%, #6F9F74);
  box-shadow: 0 10px 24px rgba(80,120,80,.18);
  animation: canopySway 5s ease-in-out infinite;
}
.tree__canopy--left { width: 112px; height: 94px; left: 6px; bottom: 150px; }
.tree__canopy--right { width: 118px; height: 98px; right: 2px; bottom: 156px; animation-delay: -1.2s; }
.tree__canopy--top { width: 142px; height: 118px; left: 50%; margin-left: -71px; bottom: 194px; animation-delay: -2.4s; }
@keyframes canopySway {
  0%, 100% { transform: translateY(0) rotate(-1deg); }
  50% { transform: translateY(-4px) rotate(1deg); }
}
.tree__roots {
  position: absolute; left: 50%; bottom: 8px; width: 180px; height: 34px;
  margin-left: -90px; border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(120,94,70,.55), rgba(120,94,70,0) 70%);
}
.capsule-falling {
  position: absolute; left: 50%; top: 0; z-index: 5;
  opacity: 0; transform: translateX(-50%);
  font-size: 30px; filter: drop-shadow(0 4px 8px rgba(90,70,50,.25));
}
.capsule-orbs { position: absolute; left: 50%; bottom: 0; width: 190px; margin-left: -95px; height: 52px; }
.capsule-orb {
  position: absolute; bottom: 4px; opacity: .85;
  animation: orbFloat 3.6s ease-in-out infinite;
  filter: drop-shadow(0 3px 6px rgba(90,70,50,.22));
}
@keyframes orbFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}
.tree-scene__ground {
  position: absolute; left: 0; right: 0; bottom: 0; height: 58px;
  background: linear-gradient(180deg, rgba(168,190,150,0), rgba(143,170,127,.55));
}
.tree-scene__hint {
  position: absolute; left: 0; right: 0; bottom: 8px;
  text-align: center; font-size: 11px; color: #6F7F68; letter-spacing: .08em;
}
.capsule-list { margin-top: 4px; }
.capsule-state { text-align: center; color: #9A8F7E; padding: 32px 16px; }
.capsule-state__emoji { font-size: 2.4rem; margin-bottom: 12px; }
.capsule-notes { display: grid; gap: 14px; }
.capsule-note { padding: 18px 20px; }
.capsule-note__head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.capsule-note__date { font-size: .78rem; color: #B0A594; }
.capsule-note__delete {
  background: none; border: none; color: #C0AFA0; font-size: .78rem; cursor: pointer;
}
.capsule-note__delete:hover { color: #C97B7B; }
.capsule-note__content { white-space: pre-wrap; line-height: 1.8; color: #5C5348; margin: 0; }

@media (max-width: 768px) {
  .capsule-view { padding: 20px 14px 80px; }
  .capsule-header { position: relative; padding-top: 30px; }
  .back-btn { left: 0; top: 0; }
  .capsule-title { font-size: 1.55rem; }
  .tree-scene { height: 260px; }
  .tree { transform: translateX(-50%) scale(.86); }
}
</style>
