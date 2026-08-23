import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import FeatureIcon from '../ui/FeatureIcon'

export default function Navbar({ showUpload = true }) {
  const { logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <nav className="glass-nav sticky top-0 z-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link to={isAuthenticated ? '/dashboard' : '/'} className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
            <FeatureIcon name="shield" className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold text-slate-900">
            Clause<span className="text-indigo-600">Guard</span>
          </span>
        </Link>

        {isAuthenticated ? (
          <div className="flex items-center gap-2">
            {showUpload && (
              <Link to="/documents/new" className="btn-primary hidden sm:inline-flex !py-2 !px-4 text-sm">
                + Upload
              </Link>
            )}
            <Link
              to="/dashboard"
              className="text-sm font-medium text-slate-600 hover:text-slate-900 px-3 py-2 rounded-xl hover:bg-slate-100 transition-colors"
            >
              Dashboard
            </Link>
            <button
              onClick={handleLogout}
              className="text-sm font-medium text-slate-600 border border-slate-200 px-3 py-2 rounded-xl hover:bg-slate-50 transition-colors"
            >
              Sign out
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 px-3 py-2 rounded-xl hover:bg-slate-100 transition-colors">
              Sign in
            </Link>
            <Link to="/register" className="btn-primary !py-2 !px-4 text-sm">
              Get started
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}
