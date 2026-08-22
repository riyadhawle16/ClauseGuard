export default function DashboardStats({ documents }) {
  const total = documents.length
  const processing = documents.filter((d) => d.processing_status === 'processing').length
  const ready = documents.filter((d) => d.processing_status === 'ready').length
  const uploaded = documents.filter((d) => d.processing_status === 'uploaded').length

  const stats = [
    { label: 'Total', value: total, color: 'text-gray-900' },
    { label: 'Ready', value: ready, color: 'text-green-700' },
    { label: 'Awaiting processing', value: uploaded, color: 'text-gray-600' },
    { label: 'Processing', value: processing, color: 'text-blue-600' },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
      {stats.map((s) => (
        <div key={s.label} className="bg-white border border-gray-200 rounded-xl px-4 py-3">
          <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
          <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
        </div>
      ))}
    </div>
  )
}
