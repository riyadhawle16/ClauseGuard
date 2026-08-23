import { useState } from 'react'
import { analyzeMissingInfo } from '../../services/missingInfoApi'
import PanelHeader from '../ui/PanelHeader'
import { getFeature } from '../../constants/features'

const STATUS_CONFIG = {
  PRESENT: { icon: '✓', label: 'Clearly identified', chipClass: 'bg-emerald-100 text-emerald-700', rowClass: 'border-emerald-100' },
  UNCLEAR: { icon: '⚠', label: 'Unclear', chipClass: 'bg-amber-100 text-amber-700', rowClass: 'border-amber-100' },
  NOT_IDENTIFIED: { icon: '?', label: 'Not clearly identified', chipClass: 'bg-slate-100 text-slate-600', rowClass: 'border-slate-100' },
}

function FlagRow({ flag }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = STATUS_CONFIG[flag.status] || STATUS_CONFIG.NOT_IDENTIFIED

  return (
    <div className={`border rounded-xl overflow-hidden ${cfg.rowClass}`}>
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-3 flex-wrap">
          <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full ${cfg.chipClass}`}>
            <span>{cfg.icon}</span>
            <span>{cfg.label}</span>
          </span>
          <span className="text-sm font-medium text-slate-800">{flag.category_name}</span>
        </div>
        <span className="text-slate-400 ml-2 shrink-0">{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && (
        <div className="px-4 pb-4 bg-slate-50 border-t border-slate-100">
          <p className="text-sm text-slate-700 mt-3 leading-relaxed">{flag.explanation}</p>
          {flag.evidence_clause_number != null && (
            <p className="text-xs text-slate-500 mt-2">
              Related clause: Clause {flag.evidence_clause_number}
              {flag.evidence_page_number != null && ` — Page ${flag.evidence_page_number}`}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default function MissingInfoPanel({ documentId, onAnalysisComplete }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const feature = getFeature('missing')

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

  const checkBtn = (
    <button
      onClick={handleCheck}
      disabled={loading}
      className="bg-teal-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
    >
      {loading ? 'Checking…' : result ? 'Re-check' : 'Run info check'}
    </button>
  )

  return (
    <div className="mt-6 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      <PanelHeader featureId="missing" action={checkBtn} />

      <div className="px-5 py-2.5 bg-amber-50 border-b border-amber-100">
        <p className="text-xs text-amber-800 leading-relaxed">
          {feature?.shortDesc} Does not determine legal validity.
        </p>
      </div>

      {error && <p className="px-5 py-3 text-sm text-red-600">{error}</p>}

      {result && (
        <div className="px-5 py-4">
          <div className="flex gap-4 mb-4 text-sm flex-wrap">
            <span className="text-emerald-700 font-semibold">✓ {result.present_count} identified</span>
            {result.unclear_count > 0 && <span className="text-amber-700 font-semibold">⚠ {result.unclear_count} unclear</span>}
            {result.not_identified_count > 0 && <span className="text-slate-600 font-semibold">? {result.not_identified_count} not found</span>}
          </div>
          <div className="space-y-2">
            {[...notIdentified, ...unclear, ...present].map((flag) => (
              <FlagRow key={flag.id} flag={flag} />
            ))}
          </div>
        </div>
      )}

      {!result && !loading && !error && (
        <div className="px-5 py-8 text-center">
          <p className="text-sm text-slate-500 max-w-sm mx-auto leading-relaxed">
            Click &ldquo;Run info check&rdquo; to see which key agreement details are present, unclear, or missing.
          </p>
        </div>
      )}
    </div>
  )
}
