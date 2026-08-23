import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env vars for the current mode so we can read VITE_API_URL
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: false,
      proxy: {
        /**
         * LOCAL DEVELOPMENT PROXY
         *
         * In dev mode, all /api/* requests are proxied to the local backend.
         * This avoids CORS issues and makes the frontend work regardless of
         * which port Vite picks (5173, 5174, 5175...).
         *
         * In production builds (Vercel), this proxy is NOT used.
         * The production frontend uses VITE_API_URL directly.
         */
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
  }
})
