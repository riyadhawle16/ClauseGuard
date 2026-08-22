import { Link } from 'react-router-dom'

export default function EmptyState() {
  return (
    <div className="text-center py-20">
      <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
        <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 className="text-base font-semibold text-gray-900 mb-1">No agreements yet</h3>
      <p className="text-sm text-gray-500 mb-6 max-w-xs mx-auto">
        Upload your first rental agreement to get started.
      </p>
      <Link
        to="/documents/new"
        className="inline-flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
      >
        <span>+</span>
        Upload Agreement
      </Link>
    </div>
  )
}
