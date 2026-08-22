import { useState } from 'react'
import api from '../../services/api'

/**
 * Semantic search panel for a processed document.
 * Calls GET /api/v1/documents/{id}/search?q=...
 * Displays retrieved clauses — no AI generation, no chat.
 */
export default function SemanticSearch({ documentId }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)  // null = not searched yet
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

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

  return (
    <div className="mt-6 bg-white border border-gray-200 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Search this Agreement</h2>
      <p className="text-xs text-gray-400 mb-4">
        Find relevant clauses by entering a question or topic.
      </p>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. What happens if I leave early?"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {error && (
        <p className="mt-3 text-sm text-red-600">{error}</p>
      )}

      {results !== null && results.length === 0 && (
        <p className="mt-4 text-sm text-gray-500">
          No relevant clauses found for your query.
        </p>
      )}

      {results && results.length > 0 && (
        <div className="mt-4 space-y-3">
          <p className="text-xs text-gray-400">{results.length} result{results.length !== 1 ? 's' : ''} found</p>
          {results.map((result) => (
            <div
              key={result.clause_id}
              className="border border-gray-100 rounded-lg p-4 bg-gray-50"
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs font-medium text-gray-500 bg-white border border-gray-200 px-2 py-0.5 rounded">
                  Clause {result.clause_number}
                </span>
                <span className="text-xs text-gray-400">Page {result.page_number}</span>
                {result.heading && (
                  <span className="text-xs font-semibold text-gray-700">{result.heading}</span>
                )}
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {result.content.length > 500
                  ? result.content.slice(0, 500) + '…'
                  : result.content}
              </p>
            </div>
          ))}
          <p className="text-xs text-gray-400 mt-2">
            ClauseGuard provides document retrieval only. Results are excerpts from your
            agreement and do not constitute legal advice.
          </p>
        </div>
      )}
    </div>
  )
}
