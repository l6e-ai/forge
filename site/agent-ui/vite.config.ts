import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const monitorUrl = process.env.VITE_MONITOR_URL || 'http://localhost:8321';
const apiUrl = process.env.VITE_API_URL || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/monitor/api': {
        target: monitorUrl,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/monitor\/api/, '/api')
      },
      '/monitor/ingest': {
        target: monitorUrl,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/monitor\/ingest/, '/ingest')
      },
      '/monitor/ws': {
        target: monitorUrl.replace('http', 'ws'),
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/monitor\/ws/, '/ws')
      },
      '/api': {
        target: apiUrl,
        changeOrigin: true,
      },
    },
  },
});


