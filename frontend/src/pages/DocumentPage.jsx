import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getDocument, deleteDocument } from '../services/documentsApi'
import api from '../services/api'
import Disclaimer from '../components/layout/Disclaimer'
import SemanticSearch from '../components/document/SemanticSearch'

const STATUS_STYLES = {
  uploaded:   { badge: 'bg-gray-100 text-gray-700',  label: 'Uploaded' },
  processing: { badge: 'bg-blue-100 text-blue-700',  label: 'Processing…' },
  ready:      { badge: 'bg-green-100 text-green-700', label: 'Ready' },
  failed:     { badge: 'bg-red-100 text-red-700',    label: 'Failed' },
}

async function fetchClauses(documentId) {
  const res = await api.get(`/api/v1/documents/${documentId}/clauses`)
  return res.data
}

async function triggerProcessing(documentId) {
  const res = await api.post(`/api/v1/documents/${documentId}/process`)
  return res.data
}

export default function DocumentPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [doc, setDoc] = useState(null)
  const [clauses, setClauses] = useState([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const [processError, setProcessError] = useState('')
  const [deleting, setDeleting] = useState(false)

  const loadDocument = useCallback(async () => {
    try {
      const data = await getDocument(id)
      setDoc(data)
      if (data.processing_status === 'ready') {
        const cls = await fetchClauses(id)
        setClauses(cls)
      }
    } catch (err) {
      setError(err.response?.status === 404 ? 'Document not found.' : 'Failed to load document.')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { loadDocument() }, [loadDocument])

  async function handleProcess() {
    setProcessError('')
    setProcessing(true)
    try {
      await triggerProcessing(id)
      // Reload document + clauses after processing
      const data = await getDocument(id)
      setDoc(data)
      if (data.processing_status === 'ready') {
        const cls = await fetchClauses(id)
        setClauses(cls)
      }
    } catch (err) {
      setProcessError(err.response?.data?.detail || 'Processing failed. Please try again.')
      // Reload doc to pick up failed status
      try { const d = await getDocument(id); setDoc(d) } catch {}
    } finally {
      setProcessing(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Delete "${doc?.title}"? This cannot be undone.`)) return
    setDeleting(true)
    try {
      await deleteDocument(id)
      navigate('/dashboard', { replace: true })
    } catch {
      alert('Failed to delete document.')
      setDeleting(false)
    }
  }

  const statusInfo = doc ? (STATUS_STYLES[doc.processing_status] || { badge: 'bg-gray-100 text-gray-600', label: doc.processing_status }) : null

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <Link to="/dashboard" className="font-bold text-gray-900">ClauseGuard</Link>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-10">
        {loading && <p className="text-gray-500">Loading…</p>}

        {!loading && error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>
        )}

        {!loading && !error && doc && (
          <>
            {/* Document header */}
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h1 className="text-xl font-bold text-gray-900">{doc.title}</h1>
                  <p className="text-sm text-gray-500 mt-1">{doc.original_filename}</p>
                </div>
                <span className={`inline-flex px-2.5 py-1 rounded text-xs font-medium ${statusInfo.badge}`}>
                  {statusInfo.label}
                </span>
              </div>

              <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-gray-500">Uploaded</dt>
                  <dd className="font-medium text-gray-800">{new Date(doc.created_at).toLocaleString('en-IN')}</dd>
                </div>
                {doc.processing_status === 'ready' && (
                  <div>
                    <dt className="text-gray-500">Clauses extracted</dt>
                    <dd className="font-medium text-gray-800">{doc.clause_count ?? clauses.length}</dd>
                  </div>
                )}
              </dl>

              {/* Status-specific content */}
              {doc.processing_status === 'uploaded' && (
                <div className="mt-5">
                  {processError && (
                    <p className="mb-3 text-sm text-red-600 bg-red-50 rounded-lg p-3">{processError}</p>
                  )}
                  <button
                    onClick={handleProcess}
                    disabled={processing}
                    className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {processing ? 'Processing…' : 'Process Document'}
                  </button>
                  <p className="mt-2 text-xs text-gray-400">
                    Extract text and clauses from this agreement.
                  </p>
                </div>
              )}

              {doc.processing_status === 'processing' && (
                <p className="mt-5 text-sm text-blue-600 bg-blue-50 rounded-lg p-3">
                  Processing in progress…
                </p>
              )}

              {doc.processing_status === 'failed' && (
                <div className="mt-5">
                  <p className="text-sm text-red-600 bg-red-50 rounded-lg p-3">
                    Processing failed.{' '}
                    {doc.processing_error || 'Please try uploading the document again.'}
                  </p>
                  <button
                    onClick={handleProcess}
                    disabled={processing}
                    className="mt-3 bg-gray-700 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50 transition-colors"
                  >
                    {processing ? 'Processing…' : 'Retry Processing'}
                  </button>
                </div>
              )}
            </div>

            {/* Extracted clauses */}
            {doc.processing_status === 'ready' && clauses.length > 0 && (
              <div className="mt-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">
                  Extracted Clauses ({clauses.length})
                </h2>
                <div className="space-y-3">
                  {clauses.map((clause) => (
                    <div key={clause.id} className="bg-white border border-gray-200 rounded-xl p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                          Clause {clause.clause_number}
                        </span>
                        <span className="text-xs text-gray-400">Page {clause.page_number}</span>
                        {clause.heading && (
                          <span className="text-xs font-medium text-gray-700 truncate">
                            {clause.heading}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-4 whitespace-pre-wrap">
                        {clause.content.length > 400
                          ? clause.content.slice(0, 400) + '…'
                          : clause.content}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Semantic Search */}
            {doc.processing_status === 'ready' && (
              <SemanticSearch documentId={id} />
            )}

            {/* Delete */}
            <div className="mt-6 flex justify-end">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-sm text-red-600 border border-red-200 px-4 py-2 rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors"
              >
                {deleting ? 'Deleting…' : 'Delete document'}
              </button>
            </div>

            <div className="mt-4">
              <Disclaimer />
            </div>
          </>
        )}
      </main>
    </div>
  )
}
