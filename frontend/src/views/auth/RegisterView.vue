<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const nickname = ref('')
const password = ref('')
const showPassword = ref(false)
const errorMsg = ref('')
const loading = ref(false)

onMounted(() => {
  if (userStore.isLoggedIn) {
    router.replace(route.query.next || '/')
  }
})

async function handleSubmit() {
  if (!nickname.value.trim()) {
    errorMsg.value = '请输入昵称'
    return
  }
  if (password.value.length < 6) {
    errorMsg.value = '密码至少 6 位'
    return
  }
  errorMsg.value = ''
  loading.value = true
  try {
    await userStore.register(nickname.value.trim(), password.value)
    router.push(route.query.next || '/')
  } catch (e) {
    errorMsg.value = e.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card card">
      <div class="auth-card__icon">🌊</div>
      <h1 class="auth-card__title">开启静屿</h1>
      <p class="auth-card__verse">"在这里，没有人会催你长大"</p>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label class="form-label">昵称</label>
          <input v-model="nickname" type="text" class="form-input" placeholder="给自己起一个温柔的名字" autocomplete="username">
        </div>

        <div class="form-group">
          <label class="form-label">密码</label>
          <div class="password-wrap">
            <input v-model="password" :type="showPassword ? 'text' : 'password'" class="form-input" placeholder="至少 6 位" autocomplete="new-password">
            <button type="button" class="password-toggle" @click="showPassword = !showPassword">{{ showPassword ? '🙈' : '👁' }}</button>
          </div>
          <p class="form-hint">密码用于加密你的日记，请务必记牢</p>
        </div>

        <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

        <button type="submit" class="btn btn--primary auth-submit" :disabled="loading">
          {{ loading ? '海风正在搭岛…' : '建立我的小岛' }}
        </button>
      </form>

      <div class="auth-card__footer">
        已经有岛了？<router-link to="/login">回到静屿</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page { min-height: 70vh; display: grid; place-items: center; padding: 40px 16px; }
.auth-card { max-width: 420px; width: 100%; padding: 40px 32px; text-align: center; }
.auth-card__icon { font-size: 48px; margin-bottom: 12px; display: inline-block; animation: float 4s ease-in-out infinite; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
.auth-card__title { font-family: var(--font-serif); font-size: 28px; font-weight: 400; letter-spacing: 0.15em; margin: 0 0 8px; }
.auth-card__verse { color: var(--color-text-muted); font-style: italic; font-family: var(--font-serif); margin: 0 0 28px; font-size: 14px; }
.auth-form { text-align: left; }
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 13px; color: var(--color-text-secondary); margin-bottom: 6px; }
.password-wrap { position: relative; }
.password-toggle { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); font-size: 18px; opacity: 0.6; }
.password-toggle:hover { opacity: 1; }
.form-hint { font-size: 12px; color: var(--color-text-muted); margin: 6px 0 0; }
.form-error { color: #C57878; font-size: 13px; margin: 8px 0; text-align: center; }
.auth-submit { width: 100%; margin-top: 12px; padding: 14px; font-size: 15px; }
.auth-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.auth-card__footer { margin-top: 24px; font-size: 14px; color: var(--color-text-muted); }
.auth-card__footer a { color: var(--color-accent-dark); font-weight: 500; }
</style>
