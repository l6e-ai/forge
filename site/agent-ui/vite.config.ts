import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Declare process to avoid requiring @types/node in the UI package
// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const process: any

const proxyTarget = process.env.VITE_PROXY_API_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
      },
      '/monitor': {
        target: proxyTarget,
        changeOrigin: true,
        ws: true,
      },
    },
  },
})


