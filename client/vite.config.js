import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@pdf-font-regular': fileURLToPath(new URL('./node_modules/@embedpdf/fonts-sc/fonts/NotoSansHans-Regular.otf', import.meta.url)),
      '@pdf-font-bold': fileURLToPath(new URL('./node_modules/@embedpdf/fonts-sc/fonts/NotoSansHans-Bold.otf', import.meta.url))
    }
  }
})
