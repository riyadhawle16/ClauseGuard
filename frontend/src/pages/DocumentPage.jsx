import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getDocument, deleteDocument } from '../services/documentsApi'
import api from '../services/api'
import Navbar from '../components/layout/Navbar'
import Disclaimer from '../components/layout/Disclaimer'
import AnalysisSummary from '../components/document/AnalysisSummary'
import AttentionPanel from '../components/document/AttentionPanel'
import MissingInfoPanel from '../components/document/MissingInfoPanel'
import ChatPanel from '../components/document/ChatPanel'
import SemanticSearch from '../components/document/SemanticSearch'
import FeatureIcon from '../components/ui/FeatureIcon'
import { getFeature } from '../constants/features'

const STATUS_CONFIG = {
  uploaded:   { badge: 'bg-amber-50 text-amber-700 border-amber-200',   label: 'Uploaded',   dot: 'bg-amber-500' },
  processing: { badge: 'bg-indigo-50 text-indigo-700 border-indigo-200', label: 'Processing', dot: 'bg-indigo-500 animate-pulse' },
  ready:      { badge: 'bg-emerald-50 text-emerald-700 border-emerald-200', label: 'Ready',   dot: 'bg-emerald-500' },
  failed:     { badge: 'bg-red-50 text-red-700 border-red-200',         label: 'Failed',     dot: 'bg-red-500' },
}

async function fetchClauses(docId) {
  const res = await api.get(`/api/v1/documents/${docId}/clauses`)
  return res.data
}

async function triggerProcessing(docId) {
  const res = await api.post(`/api/v1/documents/${docId}/process`)
  return res.data
}

async function fetchAttentionSummary(docId) {
  try {
    const res = await api.get(`/api/v1/documents/${docId}/attention`)
    return res.data
  } catch { return null }
}

async function fetchMissingInfoSummary(docId) {
  try {
    const res = await api.get(`/api/v1/documents/${docId}/missing-info`)
    return res.data
  } catch { return null }
}

export default function DocumentPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [doc, setDoc] = useState(null)
  const [clauses, setClauses] = useState([])
  const [attentionSummary, setAttentionSummary] = useState(null)
  const [missingInfoSummary, setMissingInfoSummary] = useState(null)
  const [showClauses, setShowClauses] = useState(false)

  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [processError, setProcessError] = useState('')
  const [pageError, setPageError] = useState('')
  const [deleting, setDeleting] = useState(false)

  const loadDocument = useCallback(async () => {
    setPageError('')
    try {
      const data = await getDocument(id)
      setDoc(data)
      if (data.processing_status === 'ready') {
        const [cls, attn, miss] = await Promise.all([
          fetchClauses(id),
          fetchAttentionSummary(id),
          fetchMissingInfoSummary(id),
        ])
        setClauses(cls)
        setAttentionSummary(attn)
        setMissingInfoSummary(miss)
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setPageError('Document not found.')
      } else if (err.response?.status === 401 || err.response?.status === 403) {
        setPageError('Your session has expired. Please sign in again.')
      } else {
        setPageError('Failed to load the agreement. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { loadDocument() }, [loadDocument])

  async function pollUntilReady(docId, { intervalMs = 3000, maxAttempts = 120 } = {}) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const data = await getDocument(docId)
      setDoc(data)
      if (data.processing_status === 'ready') return data
      if (data.processing_status === 'failed') {
        throw new Error(data.processing_error || 'Processing failed. The PDF may be image-only or corrupt.')
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs))
    }
    throw new Error('Processing is taking longer than expected. Please refresh the page.')
  }

  async function handleProcess() {
    setProcessError('')
    setProcessing(true)
    try {
      await triggerProcessing(id)
      setDoc((current) => current ? { ...current, processing_status: 'processing' } : current)
      const data = await pollUntilReady(id)
      if (data.processing_status === 'ready') {
        const cls = await fetchClauses(id)
        setClauses(cls)
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message
      if (err.response?.status === 422) {
        setProcessError(msg || 'Processing failed. The PDF may be image-only or corrupt.')
      } else {
        setProcessError(msg || 'Processing failed. Please try again.')
      }
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
      alert('Failed to delete this agreement. Please try again.')
      setDeleting(false)
    }
  }

  const statusCfg = doc
    ? (STATUS_CONFIG[doc.processing_status] || { badge: 'bg-gray-100 text-gray-600', label: doc.processing_status, dot: 'bg-gray-400' })
    : null

  return (
    <div className="page-bg">
      <Navbar showUpload />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8 animate-fade-in">

        {/* Loading */}
        {loading && (
          <div className="text-center py-16">
            <p className="text-gray-500 text-sm">Loading agreement…</p>
          </div>
        )}

        {/* Page error */}
        {!loading && pageError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            {pageError}
          </div>
        )}

        {!loading && !pageError && doc && (
          <>
            {/* ── Agreement overview ─────────────────────────── */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 mb-4 shadow-sm">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-3">
                <Link to="/dashboard" className="hover:text-indigo-600 font-medium">Agreements</Link>
                <span>/</span>
                <span className="text-slate-600 truncate max-w-[200px]">{doc.title}</span>
              </div>

              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0">
                  <div className="shrink-0 w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center">
                    <FeatureIcon name="extract" className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div className="min-w-0">
                    <h1 className="text-xl font-bold text-slate-900 leading-tight">{doc.title}</h1>
                    <p className="text-sm text-slate-500 mt-0.5">{doc.original_filename}</p>
                  </div>
                </div>
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border shrink-0 ${statusCfg.badge}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${statusCfg.dot}`} />
                  {statusCfg.label}
                </span>
              </div>

              <dl className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
                <div>
                  <dt className="text-xs text-gray-500">Uploaded</dt>
                  <dd className="font-medium text-gray-800 text-xs mt-0.5">
                    {new Date(doc.created_at).toLocaleString('en-IN', {
                      day: 'numeric', month: 'short', year: 'numeric',
                    })}
                  </dd>
                </div>
                {doc.processing_status === 'ready' && (
                  <div>
                    <dt className="text-xs text-gray-500">Clauses extracted</dt>
                    <dd className="font-medium text-gray-800 text-xs mt-0.5">
                      {doc.clause_count ?? clauses.length}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {doc.processing_status === 'uploaded' && (
              <div className="bg-white border border-slate-200 rounded-2xl p-5 mb-4 shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="shrink-0 w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center">
                    <FeatureIcon name="extract" className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-base font-semibold text-slate-900">Process Agreement</h2>
                    <p className="text-sm text-slate-500 mt-1 leading-relaxed">
                      {getFeature('extract')?.desc}
                    </p>
                    {processError && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">{processError}</div>
                    )}
                    <button
                      onClick={handleProcess}
                      disabled={processing}
                      className="btn-primary mt-4 !py-2"
                    >
                      {processing ? 'Processing agreement…' : 'Process Document'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {doc.processing_status === 'processing' && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-5 mb-4 flex items-center gap-3">
                <div className="w-8 h-8 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-indigo-800">Processing your agreement</p>
                  <p className="text-xs text-indigo-600 mt-0.5">Extracting clauses and building the search index — usually takes under a minute.</p>
                </div>
              </div>
            )}

            {doc.processing_status === 'failed' && (
              <div className="bg-white border border-red-200 rounded-xl p-5 mb-4">
                <p className="text-sm text-red-700 mb-3">
                  Processing failed.{' '}
                  {doc.processing_error || 'The PDF may be image-only or unreadable.'}
                </p>
                {processError && (
                  <div className="mb-3 p-3 bg-red-50 rounded-lg text-red-700 text-sm">{processError}</div>
                )}
                <button
                  onClick={handleProcess}
                  disabled={processing}
                  className="bg-gray-700 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50 transition-colors"
                >
                  {processing ? 'Processing…' : 'Retry Processing'}
                </button>
              </div>
            )}

            {doc.processing_status === 'ready' && (
              <div className="mb-6 rounded-2xl bg-gradient-to-r from-indigo-50 to-violet-50 border border-indigo-100 p-5">
                <h2 className="text-sm font-semibold text-indigo-900">Analysis toolkit</h2>
                <p className="text-xs text-indigo-700/80 mt-1 leading-relaxed">
                  Your document is ready. Use the tools below — each one focuses on a different aspect of your agreement.
                </p>
              </div>
            )}

            {doc.processing_status === 'ready' && (attentionSummary || missingInfoSummary) && (
              <AnalysisSummary attention={attentionSummary} missingInfo={missingInfoSummary} />
            )}

            {doc.processing_status === 'ready' && (
              <>
                <AttentionPanel documentId={id} onAnalysisComplete={(data) => setAttentionSummary(data)} />
                <MissingInfoPanel documentId={id} onAnalysisComplete={(data) => setMissingInfoSummary(data)} />
                <SemanticSearch documentId={id} />
                <ChatPanel documentId={id} />
              </>
            )}

            {doc.processing_status === 'ready' && clauses.length > 0 && (
              <div className="mt-6 bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
                <button
                  onClick={() => setShowClauses((p) => !p)}
                  className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center">
                      <FeatureIcon name="extract" className="w-4 h-4 text-blue-600" />
                    </div>
                    <div>
                      <span className="text-sm font-semibold text-slate-800">
                        Extracted Clauses ({clauses.length})
                      </span>
                      <p className="text-xs text-slate-500 mt-0.5">Every clause parsed from your PDF, numbered and page-referenced.</p>
                    </div>
                  </div>
                  <span className="text-slate-400">{showClauses ? '▲' : '▼'}</span>
                </button>

                {showClauses && (
                  <div className="border-t border-gray-100 divide-y divide-gray-100">
                    {clauses.map((clause) => (
                      <div key={clause.id} className="px-5 py-4">
                        <div className="flex items-center gap-2 mb-1.5">
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
                        <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                          {clause.content.length > 500
                            ? clause.content.slice(0, 500) + '…'
                            : clause.content}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ── Delete + Disclaimer ─────────────────────────────────────── */}
            <div className="mt-6 flex justify-end">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-sm text-red-500 border border-red-200 px-4 py-2 rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors"
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
