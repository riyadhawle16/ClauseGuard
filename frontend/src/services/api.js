import axios from 'axios'

/**
 * Central Axios instance for all API calls.
 *
 * LOCAL DEVELOPMENT (npm run dev):
 *   - Leave VITE_API_URL unset or empty in frontend/.env
 *   - Vite dev server proxies /api/* → http://localhost:8000 automatically
 *   - baseURL stays '' so all requests use relative paths through the proxy
 *
 * PRODUCTION (Vercel deployment):
 *   - Set VITE_API_URL in the Vercel dashboard environment variables:
 *     VITE_API_URL = https://your-app.onrender.com
 *   - This is injected at build time by Vite
 *   - baseURL becomes 'https://your-app.onrender.com'
 *   - All API calls go directly to the Render backend
 *
 * NEVER hardcode a backend URL anywhere other than this file.
 */
const baseURL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach Bearer token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cg_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 globally — clear token and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('cg_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
