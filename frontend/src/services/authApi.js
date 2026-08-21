import api from './api'

export async function register(email, password) {
  const res = await api.post('/api/v1/auth/register', { email, password })
  return res.data
}

export async function login(email, password) {
  const res = await api.post('/api/v1/auth/login', { email, password })
  return res.data
}

export async function getMe() {
  const res = await api.get('/api/v1/auth/me')
  return res.data
}
