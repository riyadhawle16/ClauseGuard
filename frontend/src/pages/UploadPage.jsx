import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadDocument } from '../services/documentsApi'
import Navbar from '../components/layout/Navbar'

const MAX_SIZE_MB = 20

export default function UploadPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)

  function validateFile(selected) {
    if (!selected) return 'Please select a file.'
    if (!selected.name.toLowerCase().endsWith('.pdf')) return 'Only PDF files are accepted.'
    if (selected.size > MAX_SIZE_MB * 1024 * 1024)
      return `File exceeds the ${MAX_SIZE_MB} MB size limit.`
    return null
  }

  function handleFileChange(e) {
    const selected = e.target.files?.[0]
    setError('')
    if (!selected) return
    const err = validateFile(selected)
    if (err) { setError(err); setFile(null); return }
    setFile(selected)
    if (!title) setTitle(selected.name.replace(/\.pdf$/i, ''))
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const selected = e.dataTransfer.files?.[0]
    if (!selected) return
    const err = validateFile(selected)
    if (err) { setError(err); return }
    setFile(selected)
    if (!title) setTitle(selected.name.replace(/\.pdf$/i, ''))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!file) { setError('Please select a PDF file.'); return }
    if (!title.trim()) { setError('Please enter a title for this agreement.'); return }

    setUploading(true)
    try {
      const doc = await uploadDocument(file, title.trim())
      navigate(`/documents/${doc.id}`)
    } catch (err) {
      const detail = err.response?.data?.detail
      if (err.response?.status === 413) {
        setError(`The file is too large. Maximum size is ${MAX_SIZE_MB} MB.`)
      } else if (err.response?.status === 422) {
        setError(detail || 'Invalid file. Please upload a valid PDF.')
      } else if (err.response?.status === 401 || err.response?.status === 403) {
        setError('Your session has expired. Please sign in again.')
      } else {
        setError('Upload failed. Please check your connection and try again.')
      }
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar showUpload={false} />

      <main className="max-w-xl mx-auto px-4 sm:px-6 py-10">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Upload Agreement</h1>
          <p className="text-sm text-gray-500 mt-1">
            Upload a rental agreement PDF to begin analysis.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">

          {/* Drop zone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              PDF File <span className="text-red-500">*</span>
            </label>
            <div
              onClick={() => !uploading && fileInputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl px-4 py-10 text-center cursor-pointer transition-colors
                ${dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400'}
                ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              {file ? (
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {(file.size / 1024 / 1024).toFixed(1)} MB
                  </p>
                </div>
              ) : (
                <>
                  <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-sm text-gray-600">
                    Drag & drop or <span className="text-blue-600 font-medium">browse</span>
                  </p>
                  <p className="text-xs text-gray-400 mt-1">PDF only · Max {MAX_SIZE_MB} MB</p>
                </>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
              disabled={uploading}
            />
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Agreement Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Mumbai Flat — Jan 2025"
              disabled={uploading}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={uploading}
            className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Uploading…' : 'Upload Agreement'}
          </button>
        </form>
      </main>
    </div>
  )
}
