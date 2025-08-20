import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const monitorUrl = process.env.VITE_MONITOR_URL || 'http://localhost:8321';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: monitorUrl,
        changeOrigin: true,
      },
      '/ingest': {
        target: monitorUrl,
        changeOrigin: true,
      },
      '/ws': {
        target: monitorUrl.replace('http', 'ws'),
        ws: true,
        changeOrigin: true,
      },
    },
  },
});


