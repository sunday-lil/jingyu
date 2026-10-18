<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import api from '@/api'

const router = useRouter()
const notes = ref([])
const loading = ref(true)
const errorMsg = ref('')

const formatDate = (str) => {
  if (!str) return ''
  const d = new Date(str)
  if (isNaN(d.getTime())) return str
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${hh}:${mm}`
}

const fetchNotes = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await api.get('/diary/corner')
    notes.value = res?.items || []
    await nextTick()
    if (document.querySelector('.corner-note')) {
      gsap.from('.corner-note', { y: 20, duration: 0.6, stagger: 0.06, ease: 'power3.out' })
    }
  } catch (e) {
    errorMsg.value = e.message || '碎碎念加载失败'
  } finally {
    loading.value = false
  }
}

const goWrite = () => router.push('/diary/write?mode=corner')

const removeNote = async (id) => {
  if (!confirm('确定要删掉这段碎碎念吗？')) return
  try {
    await api.delete(`/diary/${id}`)
    notes.value = notes.value.filter(n => n.id !== id)
  } catch (e) {
    alert(e.message || '删除失败')
  }
}

onMounted(() => {
  fetchNotes()
})

onBeforeUnmount(() => {
  gsap.killTweensOf('.corner-note')
})
</script>

<template>
  <div class="corner-view">
    <header class="corner-header">
      <button class="back-btn" @click="router.push('/diary')">← 回日记海岸</button>
      <h1 class="corner-title">🏝️ 静屿角落</h1>
      <p class="corner-verse">"不放进漂流瓶的碎碎念，都收在这里"</p>
      <button class="btn btn--primary" @click="goWrite">✍️ 写一段碎碎念</button>
    </header>

    <section class="corner-list">
      <div v-if="loading" class="corner-state">正在打开角落的小抽屉…</div>
      <div v-else-if="errorMsg" class="corner-state">{{ errorMsg }}</div>
      <div v-else-if="notes.length === 0" class="corner-state">
        <div class="corner-state__emoji">🫧</div>
        <p>这里还是空的。写一段只想自己知道的话吧。</p>
        <button class="btn btn--primary" @click="goWrite">写一段</button>
      </div>
      <ul v-else class="corner-notes">
        <li v-for="note in notes" :key="note.id" class="corner-note">
          <div class="corner-note__date">{{ formatDate(note.created_at) }}</div>
          <p class="corner-note__content">{{ note.content }}</p>
          <button class="corner-note__delete" @click="removeNote(note.id)">删掉</button>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.corner-view {
  position: relative;
  max-width: 760px;
  margin: 0 auto;
  padding: 32px 24px 90px;
}
.corner-header {
  text-align: center;
  margin-bottom: 28px;
}
.back-btn {
  position: absolute;
  left: 24px;
  background: none;
  border: none;
  color: #8B7B5E;
  cursor: pointer;
  font-size: 0.9rem;
}
.corner-title {
  font-size: 1.9rem;
  color: #5C5348;
  margin: 18px 0 8px;
}
.corner-verse {
  color: #9A8F7E;
  font-size: 0.9rem;
  margin-bottom: 18px;
}
.corner-list {
  margin-top: 8px;
}
.corner-state {
  text-align: center;
  color: #9A8F7E;
  padding: 48px 16px;
}
.corner-state__emoji {
  font-size: 2.4rem;
  margin-bottom: 12px;
}
.corner-notes {
  list-style: none;
  padding: 0;
  display: grid;
  gap: 14px;
}
.corner-note {
  position: relative;
  background: #FFFDF8;
  border: 1px solid #EDE5D8;
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 6px 18px rgba(139, 123, 94, 0.06);
}
.corner-note__date {
  font-size: 0.78rem;
  color: #B0A594;
  margin-bottom: 8px;
}
.corner-note__content {
  white-space: pre-wrap;
  line-height: 1.75;
  color: #5C5348;
  margin: 0;
}
.corner-note__delete {
  position: absolute;
  top: 14px;
  right: 16px;
  background: none;
  border: none;
  color: #C0AFA0;
  font-size: 0.78rem;
  cursor: pointer;
}
.corner-note__delete:hover {
  color: #C97B7B;
}
</style>
