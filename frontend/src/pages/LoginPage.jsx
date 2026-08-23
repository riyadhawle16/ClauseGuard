import { useState } from 'react'
import { Link, useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { login } from '../services/authApi'
import Disclaimer from '../components/layout/Disclaimer'
import FeatureIcon from '../components/ui/FeatureIcon'
import { FEATURES } from '../constants/features'

export default function LoginPage() {
  const { login: setToken, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await login(email, password)
      setToken(data.access_token)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      if (!err.response) {
        setError('Cannot connect to the server. Please make sure the backend is running.')
      } else {
        setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-bg min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-indigo-600 via-violet-600 to-indigo-800 p-12 flex-col justify-center text-white">
        <div className="max-w-md">
          <div className="flex items-center gap-2.5 mb-8">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <FeatureIcon name="shield" className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">ClauseGuard</span>
          </div>
          <h2 className="text-3xl font-bold leading-tight">Review rental agreements with confidence</h2>
          <p className="mt-3 text-indigo-100 text-sm leading-relaxed">
            Sign in to access your uploaded agreements and analysis tools.
          </p>
          <ul className="mt-8 space-y-4">
            {FEATURES.slice(0, 4).map((f) => (
              <li key={f.id} className="flex gap-3">
                <div className="shrink-0 w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center">
                  <FeatureIcon name={f.id} className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="text-sm font-semibold">{f.title}</p>
                  <p className="text-xs text-indigo-200 mt-0.5">{f.shortDesc}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-4 py-12">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-card border border-slate-200 p-8 animate-slide-up">
          <h1 className="text-2xl font-bold text-slate-900 mb-1">Welcome back</h1>
          <p className="text-slate-500 text-sm mb-6">Sign in to continue to ClauseGuard</p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" placeholder="you@example.com" />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Password</label>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="input-field" placeholder="••••••••" />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="mt-5 text-sm text-center text-slate-500">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="text-indigo-600 font-semibold hover:underline">Create one</Link>
          </p>
          <Disclaimer />
        </div>
      </div>
    </div>
  )
}
