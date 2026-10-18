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
  // 古琴弹西洋曲谱子板块（v2.3 新增，必须放在 :yin 动态段前面）
  {
    path: '/music/western',
    name: 'music-western',
    component: () => import('@/views/music/MusicWesternView.vue'),
  },
  // 身心调理（必须放在 :yin 动态段前面）
  {
    path: '/music/therapy',
    name: 'music-therapy',
    component: () => import('@/views/music/TherapyView.vue'),
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
  // 静屿角落（不放入漂流瓶的私密碎碎念）
  {
    path: '/corner',
    name: 'corner',
    component: () => import('@/views/diary/CornerView.vue'),
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
  // 个人主页（v2.3 新增）
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/profile/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  // 通知中心（v2.3 新增）
  {
    path: '/notifications',
    name: 'notifications',
    component: () => import('@/views/notification/NotificationsView.vue'),
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
