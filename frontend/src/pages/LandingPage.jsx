import { Link } from 'react-router-dom'
import Disclaimer from '../components/layout/Disclaimer'

const FEATURES = [
  { title: 'Clause Extraction', desc: 'Automatically extracts and organises every clause from your PDF.' },
  { title: 'Attention Analysis', desc: 'Flags 10 predefined categories worth reviewing before signing.' },
  { title: 'Information Check', desc: 'Identifies which common agreement details are missing or unclear.' },
  { title: 'Agreement Assistant', desc: 'Ask questions about your agreement and get grounded answers.' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <span className="text-lg font-bold text-blue-600">ClauseGuard</span>
          <div className="flex gap-2">
            <Link to="/login" className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors">
              Sign in
            </Link>
            <Link to="/register" className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 transition-colors font-medium">
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 pt-20 pb-16 text-center">
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 leading-tight">
          Understand what you&apos;re signing.
        </h1>
        <p className="mt-4 text-lg text-gray-600 max-w-xl mx-auto">
          Upload your rental agreement and ClauseGuard will extract every clause,
          flag items worth your attention, and answer your questions — before you sign.
        </p>
        <div className="mt-8 flex gap-3 justify-center">
          <Link
            to="/register"
            className="bg-blue-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors"
          >
            Analyse my agreement
          </Link>
          <Link
            to="/login"
            className="border border-gray-300 text-gray-700 px-6 py-3 rounded-xl font-medium hover:bg-gray-50 transition-colors"
          >
            Sign in
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 pb-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {FEATURES.map((f) => (
            <div key={f.title} className="border border-gray-200 rounded-xl p-5 bg-white">
              <h3 className="font-semibold text-gray-900 mb-1">{f.title}</h3>
              <p className="text-sm text-gray-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 text-center px-4">
        <Disclaimer />
      </footer>
    </div>
  )
}
