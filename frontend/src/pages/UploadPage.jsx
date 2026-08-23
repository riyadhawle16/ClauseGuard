import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadDocument } from '../services/documentsApi'
import Navbar from '../components/layout/Navbar'
import FeatureIcon from '../components/ui/FeatureIcon'
import { FEATURES } from '../constants/features'

const MAX_SIZE_MB = 20

const UPLOAD_STEPS = [
  { title: 'Upload PDF', desc: 'Select your rental agreement file (max 20 MB).' },
  { title: 'Process document', desc: 'ClauseGuard extracts every clause and builds a search index.' },
  { title: 'Run analysis', desc: 'Use attention review, missing-info check, search, and chat.' },
]

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
    <div className="page-bg">
      <Navbar showUpload={false} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8 animate-fade-in">
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">Upload Agreement</h1>
          <p className="text-sm text-slate-500 mt-2 max-w-lg leading-relaxed">
            Upload a rental agreement PDF to begin. After processing, you&apos;ll unlock clause extraction,
            attention review, missing-info checks, semantic search, and the AI assistant.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Form */}
          <form onSubmit={handleSubmit} className="lg:col-span-3 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                PDF File <span className="text-red-500">*</span>
              </label>
              <div
                onClick={() => !uploading && fileInputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-2xl px-4 py-12 text-center cursor-pointer transition-all
                  ${dragOver ? 'border-indigo-400 bg-indigo-50/50 scale-[1.01]' : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50/50'}
                  ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                {file ? (
                  <div>
                    <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center mx-auto mb-3">
                      <FeatureIcon name="extract" className="w-6 h-6 text-indigo-600" />
                    </div>
                    <p className="text-sm font-semibold text-slate-900">{file.name}</p>
                    <p className="text-xs text-slate-400 mt-1">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                  </div>
                ) : (
                  <>
                    <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
                      <FeatureIcon name="upload" className="w-6 h-6 text-slate-400" />
                    </div>
                    <p className="text-sm text-slate-600">
                      Drag & drop or <span className="text-indigo-600 font-semibold">browse files</span>
                    </p>
                    <p className="text-xs text-slate-400 mt-1">PDF only · Max {MAX_SIZE_MB} MB</p>
                  </>
                )}
              </div>
              <input ref={fileInputRef} type="file" accept=".pdf,application/pdf" onChange={handleFileChange} className="hidden" disabled={uploading} />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Agreement Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Mumbai Flat — Jan 2025"
                disabled={uploading}
                className="input-field"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">{error}</div>
            )}

            <button type="submit" disabled={uploading} className="btn-primary w-full py-3">
              {uploading ? 'Uploading…' : 'Upload & continue'}
            </button>
          </form>

          {/* Sidebar guide */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-900 mb-4">What happens after upload</h2>
              <ol className="space-y-4">
                {UPLOAD_STEPS.map((step, i) => (
                  <li key={step.title} className="flex gap-3">
                    <span className="shrink-0 w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold">
                      {i + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-slate-800">{step.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{step.desc}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>

            <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-5">
              <p className="text-xs font-semibold text-indigo-800 uppercase tracking-wide mb-3">Tools you&apos;ll unlock</p>
              <ul className="space-y-2">
                {FEATURES.map((f) => (
                  <li key={f.id} className="text-xs text-indigo-900/80 leading-relaxed">
                    <strong>{f.title}</strong> — {f.shortDesc}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
