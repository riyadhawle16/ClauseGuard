import axios from 'axios'

// When running via `npm run dev`, Vite proxies /api/* to http://localhost:8000
// so baseURL can be empty (relative).
// In production builds deployed on a real server, set VITE_API_URL to the
// backend URL (e.g. https://your-backend.render.com).
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

// On 401, clear token and redirect to login
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
