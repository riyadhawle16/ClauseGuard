import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { listDocuments, deleteDocument } from '../services/documentsApi'
import Navbar from '../components/layout/Navbar'
import DocumentCard from '../components/dashboard/DocumentCard'
import EmptyState from '../components/dashboard/EmptyState'
import DashboardStats from '../components/dashboard/DashboardStats'
import FeatureGuide from '../components/dashboard/FeatureGuide'
import FeatureIcon from '../components/ui/FeatureIcon'

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
    <div className="page-bg">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 animate-fade-in">
        {/* Welcome banner */}
        <div className="rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 p-6 sm:p-8 mb-8 text-white shadow-soft">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold">Your Agreements</h1>
              <p className="mt-1 text-indigo-100 text-sm max-w-lg">
                Upload a rental PDF, process it once, then use ClauseGuard&apos;s analysis tools to review it before signing.
              </p>
            </div>
            <Link to="/documents/new" className="inline-flex items-center justify-center gap-2 rounded-xl bg-white text-indigo-700 px-5 py-2.5 text-sm font-semibold hover:bg-indigo-50 transition-colors shadow-sm shrink-0">
              <FeatureIcon name="upload" className="w-4 h-4" />
              Upload agreement
            </Link>
          </div>
        </div>

        {loading && (
          <div className="text-center py-16">
            <div className="inline-block w-8 h-8 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-3" />
            <p className="text-slate-500 text-sm">Loading your agreements…</p>
          </div>
        )}

        {!loading && error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm mb-4">
            {error}
            <button onClick={fetchDocuments} className="ml-3 text-red-800 underline text-xs font-medium">
              Retry
            </button>
          </div>
        )}

        {!loading && !error && documents.length === 0 && (
          <>
            <FeatureGuide />
            <EmptyState />
          </>
        )}

        {!loading && !error && documents.length > 0 && (
          <>
            <DashboardStats documents={documents} />
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Recent agreements</h2>
              <span className="text-xs text-slate-400">{documents.length} total</span>
            </div>
            <div className="space-y-3">
              {documents.map((doc) => (
                <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} />
              ))}
            </div>
            <div className="mt-10">
              <FeatureGuide />
            </div>
          </>
        )}

        <p className="mt-10 text-xs text-slate-400 text-center max-w-xl mx-auto">
          ClauseGuard provides document analysis and general informational insights.
          It is not a substitute for professional legal advice.
        </p>
      </main>
    </div>
  )
}
