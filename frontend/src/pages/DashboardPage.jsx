import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { listDocuments, deleteDocument } from '../services/documentsApi'
import DocumentCard from '../components/dashboard/DocumentCard'
import EmptyState from '../components/dashboard/EmptyState'

export default function DashboardPage() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchDocuments = useCallback(async () => {
    try {
      setError('')
      const docs = await listDocuments()
      setDocuments(docs)
    } catch {
      setError('Failed to load documents. Please refresh.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchDocuments() }, [fetchDocuments])

  async function handleDelete(doc) {
    if (!window.confirm(`Delete "${doc.title}"? This cannot be undone.`)) return
    try {
      await deleteDocument(doc.id)
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id))
    } catch {
      alert('Failed to delete document. Please try again.')
    }
  }

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <span className="font-bold text-gray-900">ClauseGuard</span>
        <div className="flex items-center gap-3">
          <Link
            to="/documents/new"
            className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            + Upload
          </Link>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-600 hover:text-gray-900 border border-gray-300 px-3 py-1.5 rounded-lg transition-colors"
          >
            Sign out
          </button>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Your Agreements</h1>

        {loading && (
          <p className="text-gray-500 text-sm">Loading…</p>
        )}

        {!loading && error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && documents.length === 0 && <EmptyState />}

        {!loading && !error && documents.length > 0 && (
          <div className="space-y-3">
            {documents.map((doc) => (
              <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
