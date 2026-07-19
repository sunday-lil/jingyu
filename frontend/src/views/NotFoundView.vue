<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="not-found">
    <div class="not-found__icon">🌊</div>
    <h1 class="not-found__title">这片海没有岸</h1>
    <p class="not-found__desc">你访问的页面不存在，或者被海浪带走了</p>
    <button class="btn btn--primary" @click="router.push('/')">回到静屿</button>
  </div>
</template>

<style scoped>
.not-found {
  text-align: center;
  padding: 80px 20px;
}
.not-found__icon {
  font-size: 72px;
  margin-bottom: 20px;
  display: inline-block;
  animation: float 4s ease-in-out infinite;
}
.not-found__title {
  font-family: var(--font-serif);
  font-size: 32px;
  font-weight: 400;
  margin: 0 0 12px;
  color: var(--color-text-primary);
}
.not-found__desc {
  color: var(--color-text-muted);
  margin: 0 0 32px;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}
</style>
