import api from './api'

export async function uploadDocument(file, title) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('title', title)
  const res = await api.post('/api/v1/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function listDocuments() {
  const res = await api.get('/api/v1/documents')
  return res.data
}

export async function getDocument(id) {
  const res = await api.get(`/api/v1/documents/${id}`)
  return res.data
}

export async function deleteDocument(id) {
  await api.delete(`/api/v1/documents/${id}`)
}

// Placeholder — implemented in Phase 7
export async function getAnalysis(id) {
  const res = await api.get(`/api/v1/documents/${id}/analysis`)
  return res.data
}
