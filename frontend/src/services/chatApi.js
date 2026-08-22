import api from './api'

export async function sendMessage(documentId, message) {
  const res = await api.post(`/api/v1/documents/${documentId}/chat`, { message })
  return res.data
}

export async function getChatHistory(documentId) {
  const res = await api.get(`/api/v1/documents/${documentId}/chat`)
  return res.data
}
