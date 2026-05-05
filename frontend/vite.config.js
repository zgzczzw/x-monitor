import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 13002,
    proxy: {
      '/api': {
        target: 'http://localhost:18002',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          echarts: ['echarts', 'echarts-wordcloud'],
          vendor: ['vue', 'vue-router', 'axios'],
        },
      },
    },
  },
})
