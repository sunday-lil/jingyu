import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/RegisterView.vue'),
  },
  // 五音音乐
  {
    path: '/music',
    name: 'music-list',
    component: () => import('@/views/music/MusicListView.vue'),
  },
  {
    path: '/music/:yin',
    name: 'music-detail',
    component: () => import('@/views/music/MusicDetailView.vue'),
    props: true,
  },
  // 漂流瓶日记
  {
    path: '/diary',
    name: 'diary-list',
    component: () => import('@/views/diary/DiaryListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/diary/write',
    name: 'diary-write',
    component: () => import('@/views/diary/DiaryWriteView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/diary/pick',
    name: 'diary-pick',
    component: () => import('@/views/diary/PickBottleView.vue'),
    meta: { requiresAuth: true },
  },
  // 情绪日历
  {
    path: '/calendar',
    name: 'calendar',
    component: () => import('@/views/mood/MoodCalendarView.vue'),
    meta: { requiresAuth: true },
  },
  // AI 树洞
  {
    path: '/ai-chat',
    name: 'ai-chat',
    component: () => import('@/views/ai/AIChatView.vue'),
    meta: { requiresAuth: true },
  },
  // 精神花园
  {
    path: '/garden',
    name: 'garden',
    component: () => import('@/views/garden/GardenView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/shop',
    name: 'shop',
    component: () => import('@/views/garden/ShopView.vue'),
    meta: { requiresAuth: true },
  },
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0, behavior: 'smooth' }
  },
})

// 全局前置守卫：检查需登录页
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'login', query: { next: to.fullPath } })
  } else {
    next()
  }
})

export default router
