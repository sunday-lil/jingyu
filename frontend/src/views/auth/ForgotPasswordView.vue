<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const nickname = ref('')
const recoveryCode = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const errorMsg = ref('')
const loading = ref(false)
const done = ref(false)

async function handleSubmit() {
  if (!nickname.value.trim()) {
    errorMsg.value = '请输入昵称'
    return
  }
  const code = recoveryCode.value.trim().toUpperCase()
  if (code.length < 6) {
    errorMsg.value = '请输入恢复码'
    return
  }
  if (newPassword.value.length < 6) {
    errorMsg.value = '新密码至少 6 位'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的新密码不一致'
    return
  }
  errorMsg.value = ''
  loading.value = true
  try {
    await api.post('/auth/reset-password', {
      nickname: nickname.value.trim(),
      recovery_code: code,
      new_password: newPassword.value,
    })
    done.value = true
  } catch (e) {
    errorMsg.value = e.message || '重置失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card card">
      <div class="auth-card__icon">🔑</div>
      <h1 class="auth-card__title">{{ done ? '密码已重置' : '找回密码' }}</h1>
      <p class="auth-card__verse">
        {{ done ? '"海风记得你，回来就好。"' : '"用注册时保存的恢复码，换一把新钥匙。"' }}
      </p>

      <template v-if="done">
        <div class="reset-done">
          <p>新密码已经生效，去登录吧。</p>
          <button class="btn btn--primary auth-submit" @click="router.push('/login')">回到静屿</button>
        </div>
      </template>

      <template v-else>
        <form class="auth-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label class="form-label">昵称</label>
            <input v-model="nickname" type="text" class="form-input" placeholder="你的昵称" autocomplete="username">
          </div>

          <div class="form-group">
            <label class="form-label">恢复码</label>
            <input
              v-model="recoveryCode"
              type="text"
              class="form-input recovery-input"
              placeholder="8 位字母/数字，例如 K7M2P9QX"
              maxlength="20"
              autocomplete="one-time-code"
            >
          </div>

          <div class="form-group">
            <label class="form-label">新密码</label>
            <div class="password-wrap">
              <input
                v-model="newPassword"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                placeholder="至少 6 位"
                autocomplete="new-password"
              >
              <button type="button" class="password-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? '🙈' : '👁' }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">确认新密码</label>
            <input
              v-model="confirmPassword"
              type="password"
              class="form-input"
              placeholder="再输入一次"
              autocomplete="new-password"
            >
          </div>

          <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

          <button type="submit" class="btn btn--primary auth-submit" :disabled="loading">
            {{ loading ? '正在换钥匙…' : '重置密码' }}
          </button>
        </form>

        <p class="reset-hint">
          恢复码在注册时（或老用户首次登录时）只显示一次。<br>
          如果从没保存过，请联系岛主在后台重置密码。
        </p>
      </template>

      <div class="auth-card__footer">
        <router-link to="/login">← 回到登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page { min-height: 70vh; display: grid; place-items: center; padding: 40px 16px; }
.auth-card { max-width: 430px; width: 100%; padding: 38px 30px; text-align: center; }
.auth-card__icon { font-size: 46px; margin-bottom: 10px; display: inline-block; }
.auth-card__title { font-family: var(--font-serif); font-size: 27px; font-weight: 400; letter-spacing: .12em; margin: 0 0 8px; }
.auth-card__verse { color: var(--color-text-muted); font-style: italic; font-family: var(--font-serif); margin: 0 0 24px; font-size: 13.5px; }
.auth-form { text-align: left; }
.form-group { margin-bottom: 15px; }
.form-label { display: block; font-size: 13px; color: var(--color-text-secondary); margin-bottom: 6px; }
.form-input {
  width: 100%; box-sizing: border-box; padding: 11px 13px;
  border: 1px solid var(--color-border); border-radius: 12px;
  background: rgba(255,255,255,.7); font-family: inherit; font-size: 14px;
  color: var(--color-text-primary); outline: none;
}
.form-input:focus { border-color: var(--color-accent); }
.recovery-input { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; letter-spacing: .12em; text-transform: uppercase; }
.password-wrap { position: relative; }
.password-toggle { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); font-size: 17px; opacity: .6; background: none; border: none; cursor: pointer; }
.form-error { color: #C57878; font-size: 13px; margin: 8px 0; text-align: center; line-height: 1.6; }
.auth-submit { width: 100%; margin-top: 8px; padding: 13px; }
.reset-hint { color: #9A8F7E; font-size: 12px; line-height: 1.8; margin: 18px 0 0; text-align: center; }
.reset-done p { color: #6B5A48; line-height: 1.8; margin: 0 0 16px; }
.auth-card__footer { margin-top: 22px; font-size: 13px; color: var(--color-text-muted); }
.auth-card__footer a { color: var(--color-accent-dark); }
@media (max-width: 768px) {
  .auth-page { padding: 20px 14px 60px; }
  .auth-card { padding: 28px 20px; }
}
</style>
