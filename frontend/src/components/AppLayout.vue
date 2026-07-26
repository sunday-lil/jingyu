<script setup>
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import AmbientBackground from '@/components/AmbientBackground.vue'
import api from '@/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 移动端「更多」抽屉
const mobileMenuOpen = ref(false)

// v2.3：通知未读数（登录后定时拉取）
const unreadCount = ref(0)
let notifTimer = null
const fetchUnread = async () => {
  if (!userStore.isLoggedIn) return
  try {
    const res = await api.get('/notifications/unread')
    unreadCount.value = res?.unread || 0
  } catch {
    // 静默
  }
}
onMounted(() => {
  fetchUnread()
  notifTimer = setInterval(fetchUnread, 60_000)  // 每分钟拉一次
})
onBeforeUnmount(() => {
  if (notifTimer) clearInterval(notifTimer)
})

// 导航项（v2.3：四字文艺命名 + 岛屿图标 + 商店/Profile 入口）
const navItems = [
  { name: 'home', label: '静屿', path: '/', icon: '🏝️' },
  { name: 'music-list', label: '琴音疗心', path: '/music', icon: '🎵' },
  { name: 'diary-list', label: '漂流日记', path: '/diary', icon: '📖' },
  { name: 'diary-pick', label: '拾瓶', path: '/diary/pick', icon: '🍶' },
  { name: 'calendar', label: '情绪日历', path: '/calendar', icon: '🌙' },
  { name: 'ai-chat', label: '心语树洞', path: '/ai-chat', icon: '🌳' },
  { name: 'shop', label: '落叶画坊', path: '/shop', icon: '🍂' },
  { name: 'garden', label: '屿上花田', path: '/garden', icon: '🌸' },
  { name: 'profile', label: '我的', path: '/profile', icon: '👤' },
]

// 当前激活的导航项
const activeNav = computed(() => route.name)

// 全屏布局：移动端不显示底部 tabbar + 不应用 padding（聊天页等全屏场景）
const isFullscreen = computed(() => !!route.meta?.fullscreen)

// 移动端 tabbar：4 个固定核心 + 中央「更多」按钮
// v2.3 调整：固定 静屿 / 漂流日记 / [更多] / 情绪日历 / 我的
// 「更多」展开后访问：琴音疗心 / 拾瓶 / 心语树洞 / 落叶画坊 / 屿上花田
const tabbarFixed = computed(() => [
  navItems[0],  // 静屿
  navItems[2],  // 漂流日记
  navItems[4],  // 情绪日历
  navItems[8],  // 我的
])
const tabbarMore = computed(() => [
  navItems[1],  // 琴音疗心
  navItems[3],  // 拾瓶
  navItems[5],  // 心语树洞
  navItems[6],  // 落叶画坊
  navItems[7],  // 屿上花田
])

// 路由变化时关闭抽屉
import { watch } from 'vue'
watch(() => route.fullPath, () => {
  mobileMenuOpen.value = false
})

// 锁定背景滚动（抽屉打开时）
const toggleBodyScroll = (lock) => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = lock ? 'hidden' : ''
}

async function handleLogout() {
  await userStore.logout()
  router.push('/')
}

function go(path) {
  router.push(path)
  mobileMenuOpen.value = false
}

function toggleMoreMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
  toggleBodyScroll(mobileMenuOpen.value)
}

function closeMoreMenu() {
  mobileMenuOpen.value = false
  toggleBodyScroll(false)
}

onBeforeUnmount(() => {
  toggleBodyScroll(false)
})
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--fullscreen': isFullscreen }">
    <!-- 全局治愈系氛围背景（CSS 雾气 + Canvas2D 光点 + Three.js 粒子层渐进增强） -->
    <AmbientBackground />

    <!-- ── 桌面端（≥1025px）顶部完整导航 ── -->
    <header class="desktop-nav safe-top">
      <div class="nav-inner nav-inner--desktop">
        <router-link to="/" class="nav-brand">
          <span class="nav-brand__icon">🏝️</span>
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
            <button
              class="nav-bell"
              @click="router.push('/notifications')"
              :title="`未读通知 ${unreadCount} 条`"
              aria-label="通知"
            >
              🔔<span v-if="unreadCount > 0" class="nav-bell__badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
            </button>
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

    <!-- ── 平板（769-1024px）紧凑顶部导航 ── -->
    <header class="tablet-nav safe-top">
      <div class="nav-inner nav-inner--tablet">
        <router-link to="/" class="nav-brand">
          <span class="nav-brand__icon">🏝️</span>
          <span class="nav-brand__name">静屿</span>
        </router-link>

        <nav class="nav-links nav-links--compact">
          <router-link
            v-for="item in navItems.slice(1)"
            :key="item.name"
            :to="item.path"
            class="nav-link nav-link--compact"
            :class="{ 'is-active': activeNav === item.name }"
            :title="item.label"
          >
            <span class="nav-link__icon">{{ item.icon }}</span>
            <span class="nav-link__label--compact">{{ item.label }}</span>
          </router-link>
        </nav>

        <div class="nav-user">
          <template v-if="userStore.isLoggedIn">
            <button
              class="nav-bell"
              @click="router.push('/notifications')"
              :title="`未读通知 ${unreadCount} 条`"
              aria-label="通知"
            >
              🔔<span v-if="unreadCount > 0" class="nav-bell__badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
            </button>
            <div class="nav-energy" :title="`露水: ${userStore.energy}`">
              <span class="nav-energy__icon">💧</span>
              <span class="nav-energy__num">{{ userStore.energy }}</span>
            </div>
            <button class="nav-user__btn nav-user__btn--compact" @click="handleLogout">离开</button>
          </template>
          <template v-else>
            <router-link to="/login" class="btn btn--ghost nav-user__login">登录</router-link>
          </template>
        </div>
      </div>
    </header>

    <!-- ── 移动端（≤768px）顶部精简状态栏（fullscreen 模式隐藏） ── -->
    <header v-if="!isFullscreen" class="mobile-topbar safe-top">
      <router-link to="/" class="mobile-topbar__brand">
        <span class="mobile-topbar__icon">🏝️</span>
        <span class="mobile-topbar__name">静屿</span>
      </router-link>
      <div class="mobile-topbar__right">
        <template v-if="userStore.isLoggedIn">
          <button
            class="mobile-topbar__bell"
            @click="router.push('/notifications')"
            aria-label="通知"
          >
            🔔<span v-if="unreadCount > 0" class="mobile-topbar__bell-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
          </button>
          <div class="mobile-topbar__energy">
            <span>💧</span>
            <span>{{ userStore.energy }}</span>
          </div>
          <button class="mobile-topbar__logout" @click="handleLogout">离开</button>
        </template>
        <template v-else>
          <router-link to="/login" class="mobile-topbar__login">登录</router-link>
        </template>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content" :class="{ 'main-content--fullscreen': isFullscreen }">
      <slot />
    </main>

    <!-- ── 移动端底部 Tabbar（fullscreen 模式隐藏，避免遮挡聊天输入框等全屏内容） ── -->
    <nav v-if="!isFullscreen" class="mobile-tabbar" :class="{ 'mobile-tabbar--shifted': mobileMenuOpen }">
      <router-link
        v-for="item in tabbarFixed"
        :key="item.name"
        :to="item.path"
        class="tabbar-item"
        :class="{ 'is-active': activeNav === item.name }"
      >
        <span class="tabbar-item__icon">{{ item.icon }}</span>
        <span class="tabbar-item__label">{{ item.label }}</span>
      </router-link>

      <!-- 中央「更多」按钮 -->
      <button
        class="tabbar-item tabbar-more"
        :class="{ 'is-active': mobileMenuOpen }"
        @click="toggleMoreMenu"
        aria-label="更多入口"
      >
        <span class="tabbar-item__icon" :class="{ 'tabbar-more__icon--rotated': mobileMenuOpen }">✦</span>
        <span class="tabbar-item__label">更多</span>
      </button>
    </nav>

    <!-- 「更多」抽屉（覆盖式） -->
    <Transition name="drawer">
      <div v-if="mobileMenuOpen" class="mobile-drawer-mask" @click="closeMoreMenu">
        <nav class="mobile-drawer" @click.stop>
          <div class="mobile-drawer__header">
            <span>更多入口</span>
            <button class="mobile-drawer__close" @click="closeMoreMenu" aria-label="关闭">×</button>
          </div>
          <div class="mobile-drawer__grid">
            <button
              v-for="item in tabbarMore"
              :key="item.name"
              class="mobile-drawer__item"
              :class="{ 'is-active': activeNav === item.name }"
              @click="go(item.path)"
            >
              <span class="mobile-drawer__icon">{{ item.icon }}</span>
              <span class="mobile-drawer__label">{{ item.label }}</span>
            </button>
          </div>
        </nav>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  min-height: 100dvh;  /* iOS 16+ Safari 底部地址栏出现/消失时视口自动适配 */
  display: flex;
  flex-direction: column;
}

/* ════════════════════════════════════════
 * 桌面端（≥1025px）：完整顶部导航
 * ════════════════════════════════════════ */
.desktop-nav { display: none; }
.tablet-nav { display: none; }
.mobile-topbar { display: none; }
.mobile-tabbar { display: none; }

@media (min-width: 1025px) {
  .desktop-nav {
    display: block;
    position: sticky;
    top: 0;
    z-index: 50;
    background: rgba(249, 246, 240, 0.85);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--color-border);
  }
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}
.nav-inner--desktop { padding: 14px 32px; }
.nav-inner--tablet { padding: 10px 20px; gap: 16px; }

.nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 500;
  color: var(--color-text-primary);
  letter-spacing: 0.1em;
  flex-shrink: 0;
}
.nav-brand__icon { font-size: 22px; }

.nav-links {
  display: flex;
  gap: 4px;
  flex: 1;
  justify-content: center;
}
.nav-links--compact { gap: 2px; justify-content: center; }

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: 14px;
  transition: all 0.3s var(--ease-soft);
  white-space: nowrap;
}
.nav-link:hover {
  background: rgba(255, 255, 255, 0.6);
  color: var(--color-text-primary);
}
.nav-link.is-active {
  background: rgba(184, 165, 144, 0.15);
  color: var(--color-accent-dark);
}
.nav-link__icon { font-size: 16px; }

/* 平板紧凑：图标 + 极短标签，避免 7 项塞不下 */
.nav-link--compact {
  flex-direction: column;
  gap: 2px;
  padding: 6px 8px;
  font-size: 11px;
}
.nav-link--compact .nav-link__icon { font-size: 18px; }
.nav-link__label--compact { font-size: 11px; letter-spacing: 0.05em; }

.nav-user {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
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
.nav-energy__icon { font-size: 14px; }

/* 通知铃铛 */
.nav-bell {
  position: relative;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(200, 180, 160, 0.25);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s var(--ease-soft);
  flex-shrink: 0;
}
.nav-bell:hover {
  background: rgba(255, 255, 255, 0.85);
  transform: translateY(-1px);
}
.nav-bell__badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: #E89A9A;
  color: #fff;
  font-size: 10px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(232, 154, 154, 0.4);
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
.nav-user__btn--compact { padding: 5px 10px; font-size: 12px; }

/* ════════════════════════════════════════
 * 平板（769-1024px）：紧凑顶部导航
 * ════════════════════════════════════════ */
@media (min-width: 769px) and (max-width: 1024px) {
  .tablet-nav {
    display: block;
    position: sticky;
    top: 0;
    z-index: 50;
    background: rgba(249, 246, 240, 0.85);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--color-border);
  }
}

/* ════════════════════════════════════════
 * 主内容区
 * ════════════════════════════════════════ */
.main-content {
  flex: 1;
  width: 100%;
}

/* 桌面：减去顶部导航高度（约 64px） */
@media (min-width: 1025px) {
  .main-content {
    min-height: calc(100dvh - 64px);
  }
}

/* 平板：减去顶部紧凑导航高度（约 56px） */
@media (min-width: 769px) and (max-width: 1024px) {
  .main-content {
    min-height: calc(100dvh - 56px);
  }
}

/* 移动端：减去顶部 topbar（约 48px）+ 底部 tabbar（72px + safe-area） */
@media (max-width: 768px) {
  .main-content {
    min-height: calc(100dvh - 48px - 72px - env(safe-area-inset-bottom));
    padding-top: 48px;       /* 顶部 topbar 占位 */
    padding-bottom: calc(72px + env(safe-area-inset-bottom));  /* 底部 tabbar 占位 */
  }
  /* fullscreen 模式（如 /ai-chat）：不显示 topbar / tabbar，main 占满视口 */
  .main-content--fullscreen {
    min-height: 100dvh;
    padding-top: 0;
    padding-bottom: 0;
  }
}

/* ════════════════════════════════════════
 * 移动端（≤768px）：顶部精简状态栏 + 底部 Tabbar
 * ════════════════════════════════════════ */
@media (max-width: 768px) {
  .mobile-topbar {
    display: flex;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 50;
    height: 48px;
    padding: 0 16px;
    padding-top: env(safe-area-inset-top);  /* iPhone 刘海 / 灵动岛 */
    align-items: center;
    justify-content: space-between;
    background: rgba(249, 246, 240, 0.9);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--color-border);
  }
  .mobile-topbar__brand {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: var(--font-serif);
    font-size: 16px;
    color: var(--color-text-primary);
    letter-spacing: 0.1em;
  }
  .mobile-topbar__icon { font-size: 18px; }
  .mobile-topbar__right {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .mobile-topbar__energy {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: var(--radius-full, 999px);
    background: rgba(168, 197, 160, 0.18);
    font-size: 12px;
    color: var(--color-text-secondary);
  }
  .mobile-topbar__bell {
    position: relative;
    background: rgba(255, 255, 255, 0.5);
    border: none;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    font-size: 14px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .mobile-topbar__bell-badge {
    position: absolute;
    top: -1px;
    right: -1px;
    min-width: 15px;
    height: 15px;
    padding: 0 3px;
    border-radius: 8px;
    background: #E89A9A;
    color: #fff;
    font-size: 9px;
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .mobile-topbar__logout,
  .mobile-topbar__login {
    padding: 4px 10px;
    border-radius: var(--radius-full, 999px);
    background: rgba(255, 255, 255, 0.5);
    color: var(--color-text-muted);
    font-size: 12px;
  }

  /* 底部 tabbar：4 个固定 + 1 个「更多」 */
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
    /* iPhone home indicator 避让 */
    padding: 6px 4px calc(6px + env(safe-area-inset-bottom));
    justify-content: space-around;
    align-items: stretch;
    transition: transform 0.3s var(--ease-soft);
  }
  /* 抽屉打开时 tabbar 略微下沉，让位给抽屉 */
  .mobile-tabbar--shifted {
    transform: translateY(8px);
  }

  .tabbar-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    padding: 6px 8px;
    border-radius: var(--radius-md);
    color: var(--color-text-muted);
    font-size: 10px;
    transition: all 0.3s var(--ease-soft);
    flex: 1;
    min-width: 0;
    background: none;
    border: none;
    cursor: pointer;
  }
  .tabbar-item.is-active {
    color: var(--color-accent-dark);
  }
  .tabbar-item__icon {
    font-size: 20px;
    line-height: 1;
    transition: transform 0.3s var(--ease-soft);
  }
  .tabbar-more__icon--rotated {
    transform: rotate(135deg);
  }
  .tabbar-more.is-active {
    background: rgba(184, 165, 144, 0.15);
    color: var(--color-accent-dark);
  }

  /* 「更多」抽屉：从底部滑出，覆盖式 */
  .mobile-drawer-mask {
    position: fixed;
    inset: 0;
    z-index: 60;
    background: rgba(61, 51, 39, 0.4);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: flex-end;
  }
  .mobile-drawer {
    width: 100%;
    background: var(--color-bg-primary);
    border-radius: 24px 24px 0 0;
    padding: 16px 20px calc(20px + env(safe-area-inset-bottom));
    box-shadow: 0 -8px 32px rgba(61, 51, 39, 0.15);
  }
  .mobile-drawer__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: var(--font-serif);
    font-size: 16px;
    color: var(--color-text-primary);
    margin-bottom: 16px;
    letter-spacing: 0.1em;
  }
  .mobile-drawer__close {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    color: var(--color-text-muted);
    font-size: 22px;
    line-height: 1;
    display: grid;
    place-items: center;
  }
  .mobile-drawer__grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
  .mobile-drawer__item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 18px 8px;
    border-radius: var(--radius-lg);
    background: rgba(255, 255, 255, 0.5);
    border: 1px solid var(--color-border);
    color: var(--color-text-secondary);
    transition: all 0.3s var(--ease-soft);
  }
  .mobile-drawer__item.is-active {
    background: rgba(184, 165, 144, 0.15);
    color: var(--color-accent-dark);
  }
  .mobile-drawer__icon {
    font-size: 30px;
  }
  .mobile-drawer__label {
    font-size: 13px;
    letter-spacing: 0.05em;
  }
}

/* 抽屉过渡动画 */
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.3s var(--ease-soft);
}
.drawer-enter-active .mobile-drawer,
.drawer-leave-active .mobile-drawer {
  transition: transform 0.3s var(--ease-soft);
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from .mobile-drawer,
.drawer-leave-to .mobile-drawer {
  transform: translateY(100%);
}
</style>
