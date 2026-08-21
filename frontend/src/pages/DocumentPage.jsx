import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getDocument, deleteDocument } from '../services/documentsApi'
import Disclaimer from '../components/layout/Disclaimer'

const STATUS_STYLES = {
  uploaded:   'bg-gray-100 text-gray-700',
  processing: 'bg-blue-100 text-blue-700 animate-pulse',
  ready:      'bg-green-100 text-green-700',
  failed:     'bg-red-100 text-red-700',
}

export default function DocumentPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [doc, setDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    async function fetchDoc() {
      try {
        const data = await getDocument(id)
        setDoc(data)
      } catch (err) {
        setError(err.response?.status === 404 ? 'Document not found.' : 'Failed to load document.')
      } finally {
        setLoading(false)
      }
    }
    fetchDoc()
  }, [id])

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

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <Link to="/dashboard" className="font-bold text-gray-900">ClauseGuard</Link>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-10">
        {loading && <p className="text-gray-500">Loading…</p>}

        {!loading && error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && doc && (
          <>
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h1 className="text-xl font-bold text-gray-900">{doc.title}</h1>
                  <p className="text-sm text-gray-500 mt-1">{doc.original_filename}</p>
                </div>
                <span className={`inline-flex px-2.5 py-1 rounded text-xs font-medium ${STATUS_STYLES[doc.processing_status] || 'bg-gray-100 text-gray-600'}`}>
                  {doc.processing_status}
                </span>
              </div>

              <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-gray-500">Uploaded</dt>
                  <dd className="font-medium text-gray-800">
                    {new Date(doc.created_at).toLocaleString('en-IN')}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Last updated</dt>
                  <dd className="font-medium text-gray-800">
                    {new Date(doc.updated_at).toLocaleString('en-IN')}
                  </dd>
                </div>
              </dl>

              {doc.processing_status === 'uploaded' && (
                <p className="mt-5 text-sm text-gray-500 bg-gray-50 rounded-lg p-3">
                  Analysis features will be available after Phase 4 processing is complete.
                </p>
              )}

              {doc.processing_status === 'failed' && (
                <p className="mt-5 text-sm text-red-600 bg-red-50 rounded-lg p-3">
                  Processing failed. {doc.processing_error || 'Please try uploading again.'}
                </p>
              )}
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-sm text-red-600 border border-red-200 px-4 py-2 rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors"
              >
                {deleting ? 'Deleting…' : 'Delete document'}
              </button>
            </div>

            <div className="mt-6">
              <Disclaimer />
            </div>
          </>
        )}
      </main>
    </div>
  )
}
