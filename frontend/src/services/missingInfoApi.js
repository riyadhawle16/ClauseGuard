import api from './api'

export async function analyzeMissingInfo(documentId) {
  const res = await api.post(`/api/v1/documents/${documentId}/analyze-missing-info`)
  return res.data
}

export async function getMissingInfo(documentId) {
  const res = await api.get(`/api/v1/documents/${documentId}/missing-info`)
  return res.data
}
