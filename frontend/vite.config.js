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
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://127.0.0.1:5000',
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
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'gsap-vendor': ['gsap'],
          'three-vendor': ['three'],
        },
      },
    },
  },
}))
