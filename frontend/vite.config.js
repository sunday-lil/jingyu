import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 静屿前端配置
// 开发：vite dev server :5173，proxy /api 和 /static 到 FastAPI :5000
// 构建：输出到 ../static/dist（FastAPI 挂载）
export default defineConfig(({ command }) => ({
  // 生产环境前端构建产物会被 FastAPI 挂载到 /static/dist/
  // 仅 build 时设置 base，dev 模式用默认 '/' 避免访问路径变成 /static/dist/
  base: command === 'build' ? '/static/dist/' : '/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '127.0.0.1',
    // 开发模式 Vite 监听 :5000（用户统一访问入口）
    // FastAPI 在开发模式改到 :5001（由 start.py 设置 QI_PORT=5001）
    port: 5000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/openapi.json': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // 函数式 manualChunks：three 主体 + three/addons/* 一起归入 three-vendor
        // 这样 HeroScene / FlowerField / AudioVisualizer 等组件共享一份 OrbitControls + 后处理
        manualChunks(id) {
          if (id.includes('node_modules/three/')) return 'three-vendor'
          if (
            id.includes('node_modules/vue/') ||
            id.includes('node_modules/vue-router/') ||
            id.includes('node_modules/pinia/') ||
            id.includes('node_modules/@vue/')
          ) return 'vue-vendor'
          if (id.includes('node_modules/gsap/')) return 'gsap-vendor'
        },
      },
    },
  },
}))
