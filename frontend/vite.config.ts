import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    hmr: {
      clientPort: 3000
    },
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Remove the host header to avoid validation issues
            proxyReq.removeHeader('host');
          });
        }
      }
    }
  },
  build: {
    outDir: 'build',
    sourcemap: false,  // SECURITY: Disable source maps in production to prevent information disclosure
    minify: 'esbuild',
    // SECURITY: Enable terser options for better minification and security
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.log statements in production
        drop_debugger: true,  // Remove debugger statements
        pure_funcs: ['console.log', 'console.info', 'console.debug'],  // Remove specific console methods
      },
      format: {
        comments: false,  // Remove comments from production build
      },
    },
    rollupOptions: {
      output: {
        // SECURITY: Obfuscate chunk names to prevent information disclosure
        chunkFileNames: 'assets/js/[hash].js',
        entryFileNames: 'assets/js/[hash].js',
        assetFileNames: 'assets/[ext]/[hash].[ext]',
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'mui-vendor': ['@mui/material', '@mui/icons-material', '@mui/x-data-grid', '@mui/x-date-pickers'],
          'chart-vendor': ['chart.js', 'react-chartjs-2']
        }
      }
    },
    // SECURITY: Set chunk size warning limit to prevent large bundles
    chunkSizeWarningLimit: 1000,
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
})




