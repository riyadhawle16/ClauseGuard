/**
 * Compact summary card showing attention + missing-info counts.
 * Uses plain language — no legal conclusions.
 */
export default function AnalysisSummary({ attention, missingInfo }) {
  const hasAttention = attention && attention.flags_found > 0
  const hasMissing = missingInfo && missingInfo.total_categories > 0

  if (!hasAttention && !hasMissing) return null

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-4">
      <h2 className="text-sm font-semibold text-gray-700 mb-3">Analysis Summary</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">

        {/* Attention summary */}
        {hasAttention && (
          <div className="bg-indigo-50 rounded-lg px-3 py-2.5">
            <p className="text-xs font-medium text-indigo-700 mb-1">Attention Items</p>
            <p className="text-2xl font-bold text-indigo-900">{attention.flags_found}</p>
            <p className="text-xs text-indigo-600 mt-0.5">areas worth reviewing</p>
          </div>
        )}

        {/* Missing info summary */}
        {hasMissing && (
          <div className="bg-amber-50 rounded-lg px-3 py-2.5">
            <p className="text-xs font-medium text-amber-700 mb-1">Information Check</p>
            <div className="flex gap-3 mt-1">
              <div className="text-center">
                <p className="text-lg font-bold text-green-700">{missingInfo.present_count}</p>
                <p className="text-xs text-gray-500">found</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-amber-700">{missingInfo.unclear_count}</p>
                <p className="text-xs text-gray-500">unclear</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-gray-600">{missingInfo.not_identified_count}</p>
                <p className="text-xs text-gray-500">not found</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
