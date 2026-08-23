export default function AnalysisSummary({ attention, missingInfo }) {
  const hasAttention = attention && attention.flags_found > 0
  const hasMissing = missingInfo && missingInfo.total_categories > 0

  if (!hasAttention && !hasMissing) return null

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 mb-4 shadow-sm">
      <h2 className="text-sm font-semibold text-slate-800 mb-1">Analysis Summary</h2>
      <p className="text-xs text-slate-500 mb-4">Quick overview of your latest analysis results.</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {hasAttention && (
          <div className="bg-gradient-to-br from-indigo-50 to-violet-50 border border-indigo-100 rounded-xl px-4 py-3">
            <p className="text-xs font-semibold text-indigo-700 mb-1">Attention Review</p>
            <p className="text-3xl font-bold text-indigo-900">{attention.flags_found}</p>
            <p className="text-xs text-indigo-600 mt-0.5">areas worth reviewing</p>
          </div>
        )}
        {hasMissing && (
          <div className="bg-gradient-to-br from-teal-50 to-emerald-50 border border-teal-100 rounded-xl px-4 py-3">
            <p className="text-xs font-semibold text-teal-700 mb-1">Information Check</p>
            <div className="flex gap-4 mt-1">
              <div>
                <p className="text-lg font-bold text-emerald-700">{missingInfo.present_count}</p>
                <p className="text-xs text-slate-500">found</p>
              </div>
              <div>
                <p className="text-lg font-bold text-amber-700">{missingInfo.unclear_count}</p>
                <p className="text-xs text-slate-500">unclear</p>
              </div>
              <div>
                <p className="text-lg font-bold text-slate-600">{missingInfo.not_identified_count}</p>
                <p className="text-xs text-slate-500">not found</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
