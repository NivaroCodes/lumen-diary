import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(() => {
  const apiTarget = process.env.LUMEN_API_TARGET || 'http://127.0.0.1:8000'
  const proxy = { '/api': apiTarget, '/media': apiTarget }
  return { plugins: [react(), tailwindcss()], server: { proxy }, preview: { proxy } }
})
