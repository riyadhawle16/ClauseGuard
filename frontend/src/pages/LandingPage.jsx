import { Link } from 'react-router-dom'
import Disclaimer from '../components/layout/Disclaimer'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="text-center max-w-lg">
        <h1 className="text-4xl font-bold text-gray-900">ClauseGuard</h1>
        <p className="mt-2 text-xl text-gray-600">Understand. Protect. Negotiate.</p>
        <p className="mt-4 text-gray-500">
          Upload your rental agreement and understand exactly what you&apos;re signing.
        </p>
        <div className="mt-8 flex gap-4 justify-center">
          <Link
            to="/register"
            className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Get started
          </Link>
          <Link
            to="/login"
            className="border border-gray-300 text-gray-700 px-6 py-2.5 rounded-lg font-medium hover:bg-gray-100 transition-colors"
          >
            Sign in
          </Link>
        </div>
        <div className="mt-8">
          <Disclaimer />
        </div>
      </div>
    </div>
  )
}
