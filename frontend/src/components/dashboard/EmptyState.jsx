import { Link } from 'react-router-dom'
import { FEATURES } from '../../constants/features'
import FeatureIcon from '../ui/FeatureIcon'

export default function EmptyState() {
  return (
    <div className="text-center py-12 px-4">
      <div className="w-20 h-20 bg-gradient-to-br from-indigo-100 to-violet-100 rounded-3xl flex items-center justify-center mx-auto mb-5 shadow-sm">
        <FeatureIcon name="upload" className="w-10 h-10 text-indigo-600" />
      </div>
      <h3 className="text-xl font-bold text-slate-900 mb-2">No agreements yet</h3>
      <p className="text-sm text-slate-500 mb-8 max-w-sm mx-auto leading-relaxed">
        Upload your first rental agreement PDF. ClauseGuard will extract clauses and unlock all five analysis tools.
      </p>
      <Link to="/documents/new" className="btn-primary px-6 py-3">
        <FeatureIcon name="upload" className="w-4 h-4" />
        Upload your first agreement
      </Link>

      <div className="mt-10 max-w-md mx-auto text-left">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">What happens next</p>
        <ol className="space-y-2">
          {FEATURES.slice(0, 3).map((f, i) => (
            <li key={f.id} className="flex items-start gap-3 text-sm text-slate-600">
              <span className="shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold">
                {i + 1}
              </span>
              <span><strong className="text-slate-800">{f.title}:</strong> {f.shortDesc}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
