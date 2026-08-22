import { useState } from 'react'
import { analyzeAttention, getAttention } from '../../services/attentionApi'

/**
 * Attention Analysis panel — Phase 7.
 *
 * Shows "Analyze Agreement" button. After analysis, displays flagged clauses
 * grouped with plain-language explanations.
 *
 * Intentionally avoids alarming language. Uses "worth reviewing" framing,
 * NOT "illegal" or "risky".
 */
export default function AttentionPanel({ documentId }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState({})

  async function handleAnalyze() {
    setLoading(true)
    setError('')
    try {
      const data = await analyzeAttention(documentId)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  function toggleExpanded(flagId) {
    setExpanded((prev) => ({ ...prev, [flagId]: !prev[flagId] }))
  }

  return (
    <div className="mt-6 bg-white border border-gray-200 rounded-xl">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">
            ClauseGuard Attention Review
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Automated document review — not legal advice
          </p>
        </div>
        {!result && (
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Analysing…' : 'Analyse Agreement'}
          </button>
        )}
        {result && (
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="text-xs text-indigo-600 border border-indigo-200 px-3 py-1.5 rounded-lg hover:bg-indigo-50 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Analysing…' : 'Re-analyse'}
          </button>
        )}
      </div>

      {/* Disclaimer */}
      <div className="px-5 py-2 bg-amber-50 border-b border-amber-100">
        <p className="text-xs text-amber-700">
          This is an automated document review, not legal advice. Areas flagged below
          are based on predefined patterns and are provided for your awareness only.
        </p>
      </div>

      {error && (
        <div className="px-5 py-3 text-sm text-red-600">{error}</div>
      )}

      {/* Results */}
      {result && (
        <div className="px-5 py-4">
          {result.flags_found === 0 ? (
            <p className="text-sm text-gray-500">
              No predefined attention areas were identified in this agreement.
            </p>
          ) : (
            <>
              <p className="text-sm text-gray-600 mb-4">
                <span className="font-semibold text-gray-900">{result.flags_found}</span>
                {' '}area{result.flags_found !== 1 ? 's' : ''} worth reviewing
                {' '}across <span className="font-semibold">{result.total_clauses}</span> clauses.
              </p>

              <div className="space-y-3">
                {result.flags.map((flag) => (
                  <div
                    key={flag.id}
                    className="border border-gray-100 rounded-lg overflow-hidden"
                  >
                    <button
                      onClick={() => toggleExpanded(flag.id)}
                      className="w-full flex items-start justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="inline-block bg-indigo-100 text-indigo-700 text-xs font-medium px-2 py-0.5 rounded">
                            {flag.category_name}
                          </span>
                          <span className="text-xs text-gray-400">
                            Clause {flag.clause_number} · Page {flag.clause_page}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mt-1 font-medium">
                          {flag.title}
                        </p>
                      </div>
                      <span className="text-gray-400 ml-2 shrink-0">
                        {expanded[flag.id] ? '▲' : '▼'}
                      </span>
                    </button>

                    {expanded[flag.id] && (
                      <div className="px-4 pb-4 bg-gray-50 border-t border-gray-100">
                        <p className="text-sm text-gray-700 mt-3">{flag.explanation}</p>
                        {flag.matched_text && (
                          <p className="text-xs text-gray-500 mt-2">
                            Matched:{' '}
                            <span className="font-mono bg-white border border-gray-200 px-1.5 py-0.5 rounded text-gray-700">
                              {flag.matched_text}
                            </span>
                          </p>
                        )}
                        <p className="text-xs text-gray-400 mt-2">
                          Detection: {flag.detection_method}
                        </p>
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
        <div className="px-5 py-6 text-center">
          <p className="text-sm text-gray-500">
            Click &ldquo;Analyse Agreement&rdquo; to identify areas worth reviewing.
          </p>
        </div>
      )}
    </div>
  )
}
