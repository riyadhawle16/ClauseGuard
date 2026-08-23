import { useState, useEffect, useRef } from 'react'
import { sendMessage, getChatHistory } from '../../services/chatApi'
import PanelHeader from '../ui/PanelHeader'
import { getFeature } from '../../constants/features'

function CitationBadge({ citation }) {
  const label = [`Clause ${citation.clause_number}`, `Page ${citation.page_number}`, citation.heading].filter(Boolean).join(' · ')
  return (
    <span className="inline-block bg-sky-50 border border-sky-200 text-sky-700 text-xs px-2 py-0.5 rounded-lg mr-1 mb-1 font-medium">
      {label}
    </span>
  )
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[85%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${isUser ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-800'}`}>
          {msg.content}
        </div>
        {!isUser && msg.citations && msg.citations.length > 0 && (
          <div className="mt-2 px-1">
            <p className="text-xs text-slate-400 mb-1 font-medium">Sources from your agreement:</p>
            {msg.citations.map((cit, i) => (
              <CitationBadge key={i} citation={cit} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function ChatPanel({ documentId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const bottomRef = useRef(null)
  const feature = getFeature('chat')

  useEffect(() => {
    getChatHistory(documentId)
      .then((data) => {
        setMessages(data.messages || [])
        setHistoryLoaded(true)
      })
      .catch(() => setHistoryLoaded(true))
  }, [documentId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text) return

    setError('')
    setLoading(true)
    const userMsg = { role: 'user', content: text, citations: [], id: `temp-${Date.now()}` }
    setMessages((prev) => [...prev, userMsg])
    setInput('')

    try {
      const data = await sendMessage(documentId, text)
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: data.answer,
        citations: data.citations || [],
        id: `resp-${Date.now()}`,
      }])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get a response. Please try again.')
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
    } finally {
      setLoading(false)
    }
  }

  const suggestions = [
    'What is the notice period?',
    'Who pays for maintenance?',
    'What happens if I leave early?',
  ]

  return (
    <div className="mt-6 bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col overflow-hidden" style={{ minHeight: '440px' }}>
      <PanelHeader featureId="chat" />

      <div className="px-5 py-2.5 bg-amber-50 border-b border-amber-100">
        <p className="text-xs text-amber-800 leading-relaxed">
          {feature?.shortDesc} Not legal advice — always verify cited clauses yourself.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        {!historyLoaded && <p className="text-xs text-slate-400 text-center">Loading history…</p>}
        {historyLoaded && messages.length === 0 && (
          <div className="text-center mt-4">
            <p className="text-sm text-slate-500 mb-4">Try asking:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestions.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setInput(s)}
                  className="text-xs bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600 px-3 py-1.5 rounded-full transition-colors border border-slate-200"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <Message key={msg.id || i} msg={msg} />
        ))}
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-slate-100 rounded-2xl px-4 py-3 text-sm text-slate-400 flex items-center gap-2">
              <span className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse" />
              Thinking…
            </div>
          </div>
        )}
        {error && <p className="text-xs text-red-600 text-center my-2">{error}</p>}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="px-5 py-4 border-t border-slate-100 flex gap-2 bg-slate-50/50">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about rent, deposit, notice period…"
          disabled={loading}
          className="input-field flex-1 !bg-white"
        />
        <button type="submit" disabled={loading || !input.trim()} className="btn-primary !py-2.5 shrink-0">
          {loading ? '…' : 'Send'}
        </button>
      </form>
    </div>
  )
}
