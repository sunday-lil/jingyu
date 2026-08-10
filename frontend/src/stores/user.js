import { defineStore } from 'pinia'
import api from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    // 后端用 cookie session，前端只缓存 user 对象（避免每次都调 /me）
    user: JSON.parse(localStorage.getItem('qi_user') || 'null'),
  }),

  getters: {
    isLoggedIn: (state) => !!state.user,
    energy: (state) => state.user?.total_energy ?? 0,
    leaves: (state) => state.user?.leaves ?? 0,
    nickname: (state) => state.user?.nickname || '',
    avatar: (state) => state.user?.avatar || '🙂',
    userId: (state) => state.user?.id ?? null,
    encryptionSalt: (state) => state.user?.encryption_salt ?? null,
  },

  actions: {
    // 登录用 nickname
    async login(nickname, password) {
      const user = await api.post('/auth/login', { nickname, password })
      this.user = user
      localStorage.setItem('qi_user', JSON.stringify(user))
      return user
    },

    // 注册只用 nickname + password
    async register(nickname, password) {
      const user = await api.post('/auth/register', { nickname, password })
      this.user = user
      localStorage.setItem('qi_user', JSON.stringify(user))
      return user
    },

    // 刷新当前用户信息（从后端拉最新）
    async refreshUser() {
      if (!this.isLoggedIn) return null
      try {
        const user = await api.get('/auth/me')
        this.user = user
        localStorage.setItem('qi_user', JSON.stringify(user))
        return user
      } catch {
        this.clearLocal()
        return null
      }
    },

    // 更新本地能量显示
    updateEnergy(newTotal) {
      if (this.user) {
        this.user.total_energy = newTotal
        localStorage.setItem('qi_user', JSON.stringify(this.user))
      }
    },

    // 更新本地资源（露水 + 落叶）
    updateResources({ total_energy, leaves } = {}) {
      if (!this.user) return
      if (typeof total_energy === 'number') this.user.total_energy = total_energy
      if (typeof leaves === 'number') this.user.leaves = leaves
      localStorage.setItem('qi_user', JSON.stringify(this.user))
    },

    // 更新个人资料（头像 / 昵称）—— 同步到本地 store
    async updateProfile({ nickname, avatar } = {}) {
      const updated = await api.patch('/profile', { nickname, avatar })
      // 同步到本地 user 对象
      if (this.user) {
        if (updated?.nickname) this.user.nickname = updated.nickname
        if (updated?.avatar) this.user.avatar = updated.avatar
        localStorage.setItem('qi_user', JSON.stringify(this.user))
      }
      return updated
    },

    async logout() {
      try {
        await api.post('/auth/logout')
      } catch {
        // 忽略：本地清掉就行
      }
      this.clearLocal()
    },

    clearLocal() {
      this.user = null
      localStorage.removeItem('qi_user')
    },
  },
})
