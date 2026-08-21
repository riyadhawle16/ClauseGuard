import { useState, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { uploadDocument } from '../services/documentsApi'

const MAX_SIZE_MB = 20

export default function UploadPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function handleFileChange(e) {
    const selected = e.target.files?.[0]
    setError('')
    if (!selected) return

    if (!selected.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.')
      setFile(null)
      return
    }
    if (selected.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File exceeds the ${MAX_SIZE_MB} MB size limit.`)
      setFile(null)
      return
    }
    setFile(selected)
    if (!title) setTitle(selected.name.replace(/\.pdf$/i, ''))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!file) { setError('Please select a PDF file.'); return }
    if (!title.trim()) { setError('Please enter a title.'); return }

    setLoading(true)
    try {
      const doc = await uploadDocument(file, title.trim())
      navigate(`/documents/${doc.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <Link to="/dashboard" className="font-bold text-gray-900">ClauseGuard</Link>
      </nav>

      <main className="max-w-xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold text-gray-900">Upload Agreement</h1>
        <p className="mt-1 text-gray-500 text-sm">Upload a rental agreement PDF to begin analysis.</p>

        <form onSubmit={handleSubmit} className="mt-6 bg-white border border-gray-200 rounded-xl p-6 space-y-5">

          {/* File picker */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              PDF File <span className="text-red-500">*</span>
            </label>
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-lg px-4 py-8 text-center cursor-pointer hover:border-blue-400 transition-colors"
            >
              {file ? (
                <p className="text-sm text-gray-800 font-medium">{file.name}</p>
              ) : (
                <>
                  <p className="text-gray-500 text-sm">Click to select a PDF</p>
                  <p className="text-gray-400 text-xs mt-1">Maximum {MAX_SIZE_MB} MB</p>
                </>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Mumbai Flat — Jan 2025"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Uploading…' : 'Upload Agreement'}
          </button>
        </form>
      </main>
    </div>
  )
}
