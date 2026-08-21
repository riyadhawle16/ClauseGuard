import { Link } from 'react-router-dom'

const STATUS_STYLES = {
  uploaded:   'bg-gray-100 text-gray-700',
  processing: 'bg-blue-100 text-blue-700',
  ready:      'bg-green-100 text-green-700',
  failed:     'bg-red-100 text-red-700',
}

function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || 'bg-gray-100 text-gray-600'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${style}`}>
      {status}
    </span>
  )
}

export default function DocumentCard({ doc, onDelete }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-start justify-between gap-4">
      <div className="min-w-0 flex-1">
        <p className="font-medium text-gray-900 truncate">{doc.title}</p>
        <p className="text-xs text-gray-400 mt-0.5 truncate">{doc.original_filename}</p>
        <div className="mt-2 flex items-center gap-3">
          <StatusBadge status={doc.processing_status} />
          <span className="text-xs text-gray-400">
            {new Date(doc.created_at).toLocaleDateString('en-IN', {
              day: 'numeric', month: 'short', year: 'numeric',
            })}
          </span>
        </div>
      </div>
      <div className="flex flex-col gap-2 shrink-0">
        <Link
          to={`/documents/${doc.id}`}
          className="text-xs text-blue-600 hover:underline"
        >
          View
        </Link>
        <button
          onClick={() => onDelete(doc)}
          className="text-xs text-red-500 hover:underline text-left"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
