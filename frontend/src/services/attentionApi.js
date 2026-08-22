import api from './api'

export async function analyzeAttention(documentId) {
  const res = await api.post(`/api/v1/documents/${documentId}/analyze-attention`)
  return res.data
}

export async function getAttention(documentId) {
  const res = await api.get(`/api/v1/documents/${documentId}/attention`)
  return res.data
}
