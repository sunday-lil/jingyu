<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import AmbientBackground from '@/components/AmbientBackground.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 移动端菜单
const mobileMenuOpen = ref(false)

// 导航项（五音 + 核心模块）
const navItems = [
  { name: 'home', label: '静屿', path: '/', icon: '🌿' },
  { name: 'music-list', label: '五音', path: '/music', icon: '🎶' },
  { name: 'diary-list', label: '日记', path: '/diary', icon: '📖' },
  { name: 'diary-pick', label: '拾瓶', path: '/diary/pick', icon: '🍶' },
  { name: 'calendar', label: '日历', path: '/calendar', icon: '🌙' },
  { name: 'ai-chat', label: '树洞', path: '/ai-chat', icon: '💭' },
  { name: 'garden', label: '花园', path: '/garden', icon: '🌸' },
]

// 当前激活的导航项
const activeNav = computed(() => route.name)

// 移动端底部 tabbar 只显示 5 个核心
const tabbarItems = computed(() =>
  [navItems[0], navItems[2], navItems[4], navItems[5], navItems[6]]
)

async function handleLogout() {
  await userStore.logout()
  router.push('/')
}

function go(path) {
  router.push(path)
  mobileMenuOpen.value = false
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- 全局治愈系氛围背景（CSS 雾气 + Canvas2D 光点 + Three.js 粒子层渐进增强） -->
    <AmbientBackground />

    <!-- 桌面端顶部导航 -->
    <header class="desktop-nav safe-top">
      <div class="nav-inner">
        <router-link to="/" class="nav-brand">
          <span class="nav-brand__icon">🌿</span>
          <span class="nav-brand__name">静屿</span>
        </router-link>

        <nav class="nav-links">
          <router-link
            v-for="item in navItems.slice(1)"
            :key="item.name"
            :to="item.path"
            class="nav-link"
            :class="{ 'is-active': activeNav === item.name }"
          >
            <span class="nav-link__icon">{{ item.icon }}</span>
            <span class="nav-link__label">{{ item.label }}</span>
          </router-link>
        </nav>

        <div class="nav-user">
          <template v-if="userStore.isLoggedIn">
            <div class="nav-energy" :title="`露水: ${userStore.energy}`">
              <span class="nav-energy__icon">💧</span>
              <span class="nav-energy__num">{{ userStore.energy }}</span>
            </div>
            <button class="nav-user__btn" @click="handleLogout">离开</button>
          </template>
          <template v-else>
            <router-link to="/login" class="btn btn--ghost nav-user__login">登录</router-link>
          </template>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="flex-1 main-content">
      <slot />
    </main>

    <!-- 移动端底部 Tabbar -->
    <nav class="mobile-tabbar safe-bottom">
      <router-link
        v-for="item in tabbarItems"
        :key="item.name"
        :to="item.path"
        class="tabbar-item"
        :class="{ 'is-active': activeNav === item.name }"
      >
        <span class="tabbar-item__icon">{{ item.icon }}</span>
        <span class="tabbar-item__label">{{ item.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<style scoped>
/* 桌面导航 */
.desktop-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(249, 246, 240, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--color-border);
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 500;
  color: var(--color-text-primary);
  letter-spacing: 0.1em;
}
.nav-brand__icon {
  font-size: 22px;
}

.nav-links {
  display: flex;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: 14px;
  transition: all 0.3s var(--ease-soft);
}
.nav-link:hover {
  background: rgba(255, 255, 255, 0.6);
  color: var(--color-text-primary);
}
.nav-link.is-active {
  background: rgba(184, 165, 144, 0.15);
  color: var(--color-accent-dark);
}
.nav-link__icon {
  font-size: 16px;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-energy {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-full, 999px);
  background: rgba(168, 197, 160, 0.15);
  font-size: 14px;
  color: var(--color-text-secondary);
}
.nav-energy__icon {
  font-size: 14px;
}

.nav-user__btn {
  padding: 6px 14px;
  border-radius: var(--radius-full, 999px);
  background: rgba(255, 255, 255, 0.5);
  color: var(--color-text-muted);
  font-size: 13px;
  transition: all 0.3s;
}
.nav-user__btn:hover {
  background: rgba(255, 255, 255, 0.8);
  color: var(--color-text-primary);
}

.main-content {
  width: 100%;
  min-height: calc(100vh - 64px);  /* 减去顶部导航高度 */
  padding-bottom: 100px;  /* 给移动端 tabbar 留空 */
}

/* 移动端底部 Tabbar */
.mobile-tabbar {
  display: none;
}

/* 响应式：移动端切换到 tabbar */
@media (max-width: 768px) {
  .desktop-nav { display: none; }
  .main-content {
    padding-bottom: 90px;  /* tabbar 高度 + 安全区 */
  }
  .mobile-tabbar {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 50;
    background: rgba(249, 246, 240, 0.95);
    backdrop-filter: blur(20px);
    border-top: 1px solid var(--color-border);
    padding: 8px 4px;
    justify-content: space-around;
  }
  .tabbar-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    padding: 6px 10px;
    border-radius: var(--radius-md);
    color: var(--color-text-muted);
    font-size: 11px;
    transition: all 0.3s var(--ease-soft);
  }
  .tabbar-item.is-active {
    color: var(--color-accent-dark);
  }
  .tabbar-item__icon {
    font-size: 22px;
  }
}
</style>
