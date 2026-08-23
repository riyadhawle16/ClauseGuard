export default function DashboardStats({ documents }) {
  const total = documents.length
  const processing = documents.filter((d) => d.processing_status === 'processing').length
  const ready = documents.filter((d) => d.processing_status === 'ready').length
  const uploaded = documents.filter((d) => d.processing_status === 'uploaded').length

  const stats = [
    { label: 'Total agreements', value: total, color: 'text-slate-900', bg: 'from-slate-50 to-white', border: 'border-slate-200' },
    { label: 'Ready to analyse', value: ready, color: 'text-emerald-700', bg: 'from-emerald-50/80 to-white', border: 'border-emerald-200' },
    { label: 'Awaiting processing', value: uploaded, color: 'text-amber-700', bg: 'from-amber-50/80 to-white', border: 'border-amber-200' },
    { label: 'Processing now', value: processing, color: 'text-indigo-700', bg: 'from-indigo-50/80 to-white', border: 'border-indigo-200' },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
      {stats.map((s) => (
        <div
          key={s.label}
          className={`rounded-2xl border ${s.border} bg-gradient-to-br ${s.bg} px-4 py-4 shadow-sm card-hover`}
        >
          <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
          <p className="text-xs text-slate-500 mt-1 font-medium">{s.label}</p>
        </div>
      ))}
    </div>
  )
}
