import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      'three/addons': 'three/examples/jsm'
    },
  },
  server: {
    port: 5173,
    proxy: {
      // 注意：必须是 '/api/' 而不是 '/api'——后者会把 /api-center 等前端路由也代理到后端（刷新即 404）
      '/api/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\//, '/'),
      },
    },
  },
})