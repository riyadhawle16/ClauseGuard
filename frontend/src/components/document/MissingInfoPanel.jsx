import { useState } from 'react'
import { analyzeMissingInfo } from '../../services/missingInfoApi'

/**
 * Missing / Unclear Information panel — Phase 8.
 *
 * Information-completeness detector only.
 * Uses plain language — no alarming labels, no legal conclusions.
 */
const STATUS_CONFIG = {
  PRESENT: {
    icon: '✓',
    label: 'Clearly identified',
    chipClass: 'bg-green-100 text-green-700',
    rowClass: 'border-green-100',
  },
  UNCLEAR: {
    icon: '⚠',
    label: 'Unclear',
    chipClass: 'bg-amber-100 text-amber-700',
    rowClass: 'border-amber-100',
  },
  NOT_IDENTIFIED: {
    icon: '?',
    label: 'Not clearly identified',
    chipClass: 'bg-gray-100 text-gray-600',
    rowClass: 'border-gray-100',
  },
}

function FlagRow({ flag }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = STATUS_CONFIG[flag.status] || STATUS_CONFIG.NOT_IDENTIFIED

  return (
    <div className={`border rounded-lg overflow-hidden ${cfg.rowClass}`}>
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3 flex-wrap">
          <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded ${cfg.chipClass}`}>
            <span>{cfg.icon}</span>
            <span>{cfg.label}</span>
          </span>
          <span className="text-sm font-medium text-gray-800">{flag.category_name}</span>
        </div>
        <span className="text-gray-400 ml-2 shrink-0">{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 bg-gray-50 border-t border-gray-100">
          <p className="text-sm text-gray-700 mt-3">{flag.explanation}</p>
          {flag.evidence_clause_number != null && (
            <p className="text-xs text-gray-500 mt-2">
              Related clause: Clause {flag.evidence_clause_number}
              {flag.evidence_page_number != null && ` — Page ${flag.evidence_page_number}`}
            </p>
          )}
          <p className="text-xs text-gray-400 mt-1">Detection: {flag.detection_method}</p>
        </div>
      )}
    </div>
  )
}

export default function MissingInfoPanel({ documentId, onAnalysisComplete }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleCheck() {
    setLoading(true)
    setError('')
    try {
      const data = await analyzeMissingInfo(documentId)
      setResult(data)
      if (onAnalysisComplete) onAnalysisComplete(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Check failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const notIdentified = result?.flags.filter((f) => f.status === 'NOT_IDENTIFIED') ?? []
  const unclear = result?.flags.filter((f) => f.status === 'UNCLEAR') ?? []
  const present = result?.flags.filter((f) => f.status === 'PRESENT') ?? []

  return (
    <div className="mt-6 bg-white border border-gray-200 rounded-xl">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">
            Information Completeness Check
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Identifies which agreement details could not be clearly found
          </p>
        </div>
        {!result && (
          <button
            onClick={handleCheck}
            disabled={loading}
            className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Checking agreement…' : 'Check Missing Information'}
          </button>
        )}
        {result && (
          <button
            onClick={handleCheck}
            disabled={loading}
            className="text-xs text-teal-600 border border-teal-200 px-3 py-1.5 rounded-lg hover:bg-teal-50 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Checking…' : 'Re-check'}
          </button>
        )}
      </div>

      {/* Disclaimer */}
      <div className="px-5 py-2 bg-amber-50 border-b border-amber-100">
        <p className="text-xs text-amber-700">
          This check identifies information that could not be clearly found in the uploaded
          document. It does not determine whether the agreement is complete or legally valid.
        </p>
      </div>

      {error && <p className="px-5 py-3 text-sm text-red-600">{error}</p>}

      {/* Results */}
      {result && (
        <div className="px-5 py-4">
          {/* Summary */}
          <div className="flex gap-4 mb-4 text-sm flex-wrap">
            <span className="text-green-700 font-medium">
              ✓ {result.present_count} identified
            </span>
            {result.unclear_count > 0 && (
              <span className="text-amber-700 font-medium">
                ⚠ {result.unclear_count} unclear
              </span>
            )}
            {result.not_identified_count > 0 && (
              <span className="text-gray-600 font-medium">
                ? {result.not_identified_count} not found
              </span>
            )}
          </div>

          {/* Flags grouped by status */}
          {[...notIdentified, ...unclear, ...present].length > 0 && (
            <div className="space-y-2">
              {[...notIdentified, ...unclear, ...present].map((flag) => (
                <FlagRow key={flag.id} flag={flag} />
              ))}
            </div>
          )}
        </div>
      )}

      {!result && !loading && !error && (
        <div className="px-5 py-6 text-center">
          <p className="text-sm text-gray-500">
            Click &ldquo;Check Missing Information&rdquo; to see which agreement
            details could be clearly identified.
          </p>
        </div>
      )}
    </div>
  )
}
