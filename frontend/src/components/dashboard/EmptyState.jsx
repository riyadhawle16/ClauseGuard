import { Link } from 'react-router-dom'

export default function EmptyState() {
  return (
    <div className="text-center py-16">
      <p className="text-gray-500">You haven&apos;t uploaded any agreements yet.</p>
      <Link
        to="/documents/new"
        className="mt-4 inline-block bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
      >
        Upload your first agreement
      </Link>
    </div>
  )
}
