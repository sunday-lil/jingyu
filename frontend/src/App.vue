<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import AppLayout from '@/components/AppLayout.vue'

const userStore = useUserStore()

onMounted(() => {
  // 启动时刷新用户信息（同步能量、登录态有效性）
  userStore.refreshUser()
})
</script>

<template>
  <AppLayout>
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </AppLayout>
</template>
