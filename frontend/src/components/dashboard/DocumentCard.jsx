import { Link } from 'react-router-dom'

const STATUS_CONFIG = {
  uploaded:   { badge: 'bg-gray-100 text-gray-600',   label: 'Uploaded',    dot: 'bg-gray-400' },
  processing: { badge: 'bg-blue-100 text-blue-700',   label: 'Processing',  dot: 'bg-blue-500 animate-pulse' },
  ready:      { badge: 'bg-green-100 text-green-700', label: 'Ready',       dot: 'bg-green-500' },
  failed:     { badge: 'bg-red-100 text-red-700',     label: 'Failed',      dot: 'bg-red-500' },
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.uploaded
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium ${cfg.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}

export default function DocumentCard({ doc, onDelete }) {
  const isReady = doc.processing_status === 'ready'

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 hover:border-gray-300 transition-colors">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="shrink-0 w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
          <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-semibold text-gray-900 truncate text-sm">{doc.title}</p>
              <p className="text-xs text-gray-400 mt-0.5 truncate">{doc.original_filename}</p>
            </div>
            <StatusBadge status={doc.processing_status} />
          </div>

          {/* Meta row */}
          <div className="mt-2 flex items-center gap-3 flex-wrap text-xs text-gray-500">
            <span>
              {new Date(doc.created_at).toLocaleDateString('en-IN', {
                day: 'numeric', month: 'short', year: 'numeric',
              })}
            </span>
            {isReady && doc.clause_count != null && (
              <span className="text-gray-400">·</span>
            )}
            {isReady && doc.clause_count != null && (
              <span>{doc.clause_count} clauses</span>
            )}
          </div>

          {/* Actions */}
          <div className="mt-3 flex items-center gap-2">
            <Link
              to={`/documents/${doc.id}`}
              className="inline-flex items-center gap-1 bg-blue-600 text-white text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Open Agreement
            </Link>
            <button
              onClick={() => onDelete(doc)}
              className="text-xs text-gray-500 hover:text-red-600 px-2 py-1.5 rounded-lg hover:bg-red-50 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
