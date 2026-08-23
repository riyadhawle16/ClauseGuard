import { Link } from 'react-router-dom'
import FeatureIcon from '../ui/FeatureIcon'

const STATUS_CONFIG = {
  uploaded:   { badge: 'bg-amber-50 text-amber-700 border-amber-200',   label: 'Uploaded',   dot: 'bg-amber-500' },
  processing: { badge: 'bg-indigo-50 text-indigo-700 border-indigo-200', label: 'Processing', dot: 'bg-indigo-500 animate-pulse' },
  ready:      { badge: 'bg-emerald-50 text-emerald-700 border-emerald-200', label: 'Ready',   dot: 'bg-emerald-500' },
  failed:     { badge: 'bg-red-50 text-red-700 border-red-200',         label: 'Failed',     dot: 'bg-red-500' },
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.uploaded
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${cfg.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}

export default function DocumentCard({ doc, onDelete }) {
  const isReady = doc.processing_status === 'ready'

  return (
    <div className="card-hover bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
      <div className="flex items-start gap-4">
        <div className="shrink-0 w-12 h-12 bg-gradient-to-br from-indigo-100 to-violet-100 rounded-xl flex items-center justify-center">
          <FeatureIcon name="extract" className="w-6 h-6 text-indigo-600" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-semibold text-slate-900 truncate">{doc.title}</p>
              <p className="text-xs text-slate-400 mt-0.5 truncate">{doc.original_filename}</p>
            </div>
            <StatusBadge status={doc.processing_status} />
          </div>

          <div className="mt-2 flex items-center gap-3 flex-wrap text-xs text-slate-500">
            <span>
              {new Date(doc.created_at).toLocaleDateString('en-IN', {
                day: 'numeric', month: 'short', year: 'numeric',
              })}
            </span>
            {isReady && doc.clause_count != null && (
              <>
                <span className="text-slate-300">·</span>
                <span className="font-medium text-indigo-600">{doc.clause_count} clauses extracted</span>
              </>
            )}
            {!isReady && doc.processing_status === 'uploaded' && (
              <>
                <span className="text-slate-300">·</span>
                <span className="text-amber-600">Needs processing</span>
              </>
            )}
          </div>

          <div className="mt-4 flex items-center gap-2">
            <Link
              to={`/documents/${doc.id}`}
              className="btn-primary !py-2 !px-4 text-xs"
            >
              Open agreement
            </Link>
            <button
              onClick={() => onDelete(doc)}
              className="text-xs font-medium text-slate-500 hover:text-red-600 px-3 py-2 rounded-xl hover:bg-red-50 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
