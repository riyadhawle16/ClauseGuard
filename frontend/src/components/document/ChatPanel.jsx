import { useState, useEffect, useRef } from 'react'
import { sendMessage, getChatHistory } from '../../services/chatApi'

function CitationBadge({ citation }) {
  const label = [
    `Clause ${citation.clause_number}`,
    `Page ${citation.page_number}`,
    citation.heading,
  ]
    .filter(Boolean)
    .join(' · ')
  return (
    <span className="inline-block bg-blue-50 border border-blue-200 text-blue-700 text-xs px-2 py-0.5 rounded mr-1 mb-1">
      {label}
    </span>
  )
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div
          className={`rounded-xl px-4 py-3 text-sm ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {msg.content}
        </div>
        {!isUser && msg.citations && msg.citations.length > 0 && (
          <div className="mt-1.5 px-1">
            <p className="text-xs text-gray-400 mb-1">Sources:</p>
            {msg.citations.map((cit, i) => (
              <CitationBadge key={i} citation={cit} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Chat panel for asking questions about a processed document.
 * Uses POST /api/v1/documents/{id}/chat and GET for history.
 * No streaming, no WebSockets — plain REST.
 */
export default function ChatPanel({ documentId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const bottomRef = useRef(null)

  // Load history on mount
  useEffect(() => {
    getChatHistory(documentId)
      .then((data) => {
        setMessages(data.messages || [])
        setHistoryLoaded(true)
      })
      .catch(() => setHistoryLoaded(true))
  }, [documentId])

  // Scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text) return

    setError('')
    setLoading(true)

    // Optimistically add user message
    const userMsg = { role: 'user', content: text, citations: [], id: `temp-${Date.now()}` }
    setMessages((prev) => [...prev, userMsg])
    setInput('')

    try {
      const data = await sendMessage(documentId, text)
      const assistantMsg = {
        role: 'assistant',
        content: data.answer,
        citations: data.citations || [],
        id: `resp-${Date.now()}`,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get a response. Please try again.')
      // Remove the optimistic user message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-6 bg-white border border-gray-200 rounded-xl flex flex-col" style={{ minHeight: '420px' }}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100">
        <h2 className="text-base font-semibold text-gray-900">ClauseGuard AI Assistant</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Ask anything about this agreement.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="px-5 py-2 bg-amber-50 border-b border-amber-100">
        <p className="text-xs text-amber-700">
          ClauseGuard explains the contents of your uploaded agreement in plain language.
          It does not provide legal advice.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {!historyLoaded && (
          <p className="text-xs text-gray-400 text-center">Loading history…</p>
        )}
        {historyLoaded && messages.length === 0 && (
          <p className="text-xs text-gray-400 text-center mt-4">
            No messages yet. Ask a question about this agreement.
          </p>
        )}
        {messages.map((msg, i) => (
          <Message key={msg.id || i} msg={msg} />
        ))}
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-100 rounded-xl px-4 py-3 text-sm text-gray-400">
              Thinking…
            </div>
          </div>
        )}
        {error && (
          <p className="text-xs text-red-600 text-center my-2">{error}</p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="px-5 py-4 border-t border-gray-100 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question, e.g. What is the notice period?"
          disabled={loading}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
        >
          {loading ? '…' : 'Send'}
        </button>
      </form>
    </div>
  )
}
