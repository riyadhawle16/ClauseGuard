import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,  // allow fallback ports (5174, 5175...) without errors
    proxy: {
      // Proxy all /api requests to the backend regardless of which port Vite is on.
      // This eliminates CORS issues and port mismatch problems entirely.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
