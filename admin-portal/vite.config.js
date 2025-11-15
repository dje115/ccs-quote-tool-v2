import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 3010,
    strictPort: false,
    hmr: {
      clientPort: 3010
    },
    // Allow all hosts to fix "Invalid host header" error
    allowedHosts: [
      'localhost',
      '.localhost',
      '127.0.0.1',
      '0.0.0.0'
    ],
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Remove the host header to avoid validation issues
            proxyReq.removeHeader('host');
          });
        }
      }
    }
  }
})
