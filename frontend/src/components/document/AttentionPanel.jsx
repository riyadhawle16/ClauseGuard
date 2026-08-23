import { useState } from 'react'
import { analyzeAttention } from '../../services/attentionApi'
import PanelHeader from '../ui/PanelHeader'
import { getFeature } from '../../constants/features'

export default function AttentionPanel({ documentId, onAnalysisComplete }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState({})
  const feature = getFeature('attention')

  async function handleAnalyze() {
    setLoading(true)
    setError('')
    try {
      const data = await analyzeAttention(documentId)
      setResult(data)
      if (onAnalysisComplete) onAnalysisComplete(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  function toggleExpanded(flagId) {
    setExpanded((prev) => ({ ...prev, [flagId]: !prev[flagId] }))
  }

  const analyzeBtn = (
    <button
      onClick={handleAnalyze}
      disabled={loading}
      className="bg-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
    >
      {loading ? 'Analysing…' : result ? 'Re-analyse' : 'Run attention review'}
    </button>
  )

  return (
    <div className="mt-6 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      <PanelHeader featureId="attention" action={analyzeBtn} />

      <div className="px-5 py-2.5 bg-amber-50 border-b border-amber-100">
        <p className="text-xs text-amber-800 leading-relaxed">
          {feature?.desc?.split('.')[0]}. Automated review only — not legal advice.
        </p>
      </div>

      {error && <div className="px-5 py-3 text-sm text-red-600">{error}</div>}

      {result && (
        <div className="px-5 py-4">
          {result.flags_found === 0 ? (
            <p className="text-sm text-slate-500">
              No predefined attention areas were identified in this agreement.
            </p>
          ) : (
            <>
              <p className="text-sm text-slate-600 mb-4">
                <span className="font-bold text-indigo-700">{result.flags_found}</span>
                {' '}area{result.flags_found !== 1 ? 's' : ''} worth reviewing across{' '}
                <span className="font-semibold">{result.total_clauses}</span> clauses.
              </p>
              <div className="space-y-3">
                {result.flags.map((flag) => (
                  <div key={flag.id} className="border border-slate-100 rounded-xl overflow-hidden">
                    <button
                      onClick={() => toggleExpanded(flag.id)}
                      className="w-full flex items-start justify-between px-4 py-3 text-left hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="inline-block bg-indigo-100 text-indigo-700 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                            {flag.category_name}
                          </span>
                          <span className="text-xs text-slate-400">
                            Clause {flag.clause_number} · Page {flag.clause_page}
                          </span>
                        </div>
                        <p className="text-sm text-slate-800 mt-1 font-medium">{flag.title}</p>
                      </div>
                      <span className="text-slate-400 ml-2 shrink-0">{expanded[flag.id] ? '▲' : '▼'}</span>
                    </button>
                    {expanded[flag.id] && (
                      <div className="px-4 pb-4 bg-slate-50 border-t border-slate-100">
                        <p className="text-sm text-slate-700 mt-3 leading-relaxed">{flag.explanation}</p>
                        {flag.matched_text && (
                          <p className="text-xs text-slate-500 mt-2">
                            Matched:{' '}
                            <span className="font-mono bg-white border border-slate-200 px-1.5 py-0.5 rounded text-slate-700">
                              {flag.matched_text}
                            </span>
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {!result && !loading && !error && (
        <div className="px-5 py-8 text-center">
          <p className="text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
            Click &ldquo;Run attention review&rdquo; to scan for clauses matching common rental review patterns.
          </p>
        </div>
      )}
    </div>
  )
}
