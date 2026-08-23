import { useState } from 'react'
import api from '../../services/api'
import PanelHeader from '../ui/PanelHeader'
import { getFeature } from '../../constants/features'

export default function SemanticSearch({ documentId }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const feature = getFeature('search')

  async function handleSearch(e) {
    e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) {
      setError('Please enter a search query.')
      return
    }
    setError('')
    setLoading(true)
    setResults(null)
    try {
      const res = await api.get(`/api/v1/documents/${documentId}/search`, {
        params: { q: trimmed, top_k: 5 },
      })
      setResults(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const examples = ['early termination', 'security deposit', 'maintenance responsibility']

  return (
    <div className="mt-6 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      <PanelHeader featureId="search" />

      <div className="px-5 py-4">
        <p className="text-xs text-slate-500 mb-4 leading-relaxed">{feature?.desc}</p>

        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. What happens if I leave early?"
            className="input-field flex-1"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !query.trim()} className="bg-violet-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-violet-700 disabled:opacity-50 transition-colors shrink-0">
            {loading ? 'Searching…' : 'Search'}
          </button>
        </form>

        <div className="mt-3 flex flex-wrap gap-2">
          {examples.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => setQuery(ex)}
              className="text-xs text-violet-600 bg-violet-50 hover:bg-violet-100 px-2.5 py-1 rounded-full transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

        {results !== null && results.length === 0 && (
          <p className="mt-4 text-sm text-slate-500">No relevant clauses found for your query.</p>
        )}

        {results && results.length > 0 && (
          <div className="mt-4 space-y-3">
            <p className="text-xs font-medium text-slate-400">{results.length} matching clause{results.length !== 1 ? 's' : ''}</p>
            {results.map((result) => (
              <div key={result.clause_id} className="border border-violet-100 rounded-xl p-4 bg-violet-50/30">
                <div className="flex items-center gap-3 mb-2 flex-wrap">
                  <span className="text-xs font-semibold text-violet-700 bg-violet-100 px-2.5 py-0.5 rounded-full">
                    Clause {result.clause_number}
                  </span>
                  <span className="text-xs text-slate-400">Page {result.page_number}</span>
                  {result.heading && <span className="text-xs font-semibold text-slate-700">{result.heading}</span>}
                </div>
                <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
                  {result.content.length > 500 ? result.content.slice(0, 500) + '…' : result.content}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
