import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { listDocuments, deleteDocument } from '../services/documentsApi'
import Navbar from '../components/layout/Navbar'
import DocumentCard from '../components/dashboard/DocumentCard'
import EmptyState from '../components/dashboard/EmptyState'
import DashboardStats from '../components/dashboard/DashboardStats'

export default function DashboardPage() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchDocuments = useCallback(async () => {
    try {
      setError('')
      const docs = await listDocuments()
      setDocuments(docs)
    } catch (err) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        setError('Your session has expired. Please sign in again.')
      } else {
        setError('Failed to load your agreements. Please refresh.')
      }
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
      alert('Failed to delete this agreement. Please try again.')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Your Agreements</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Upload, process, and analyse your rental agreements.
            </p>
          </div>
          <Link
            to="/documents/new"
            className="inline-flex items-center gap-1.5 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <span>+</span>
            Upload
          </Link>
        </div>

        {/* Loading */}
        {loading && (
          <div className="text-center py-16">
            <p className="text-gray-500 text-sm">Loading your agreements…</p>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm mb-4">
            {error}
            <button
              onClick={fetchDocuments}
              className="ml-3 text-red-800 underline text-xs"
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty */}
        {!loading && !error && documents.length === 0 && <EmptyState />}

        {/* Stats + List */}
        {!loading && !error && documents.length > 0 && (
          <>
            <DashboardStats documents={documents} />
            <div className="space-y-3">
              {documents.map((doc) => (
                <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} />
              ))}
            </div>
          </>
        )}

        {/* Legal disclaimer at bottom */}
        <p className="mt-10 text-xs text-gray-400 text-center max-w-xl mx-auto">
          ClauseGuard provides document analysis and general informational insights.
          It is not a substitute for professional legal advice.
        </p>
      </main>
    </div>
  )
}
