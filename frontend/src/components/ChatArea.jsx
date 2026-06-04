import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'

export default function ChatArea({ messages, onSend, isLoading, caseStatus }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef()

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function handleSend() {
    const text = input.trim()
    if (!text || isLoading) return
    setInput('')
    onSend(text)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 bg-gray-50">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-gray-400">
              <div className="text-5xl mb-3">💬</div>
              <p className="text-sm">Start the conversation</p>
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <MessageBubble key={i} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
          ))
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start mb-3">
            <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center text-sm mr-2 flex-shrink-0">
              🏢
            </div>
            <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-tl-sm shadow-sm">
              <div className="flex gap-1 items-center h-4">
                {[0, 150, 300].map(d => (
                  <div key={d} className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce"
                    style={{ animationDelay: `${d}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Case complete banner */}
      {caseStatus === 'complete' && (
        <div className="bg-green-50 border-t border-green-200 px-6 py-3 flex items-center gap-2">
          <span className="text-green-600 text-lg">✅</span>
          <p className="text-sm text-green-800 font-medium">
            All documents have been submitted. Your case is complete.
          </p>
        </div>
      )}

      {/* Input bar */}
      <div className="border-t border-gray-200 bg-white px-4 py-3 flex items-end gap-3">
        <textarea
          rows={1}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || caseStatus === 'complete'}
          placeholder={caseStatus === 'complete' ? 'Case complete' : 'Type a message… (Enter to send)'}
          className="flex-1 resize-none input-field min-h-[42px] max-h-32 py-2.5 disabled:bg-gray-50 disabled:text-gray-400"
          style={{ overflowY: input.split('\n').length > 3 ? 'auto' : 'hidden' }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading || caseStatus === 'complete'}
          className="btn-primary px-4 py-2.5 flex-shrink-0 flex items-center gap-2"
        >
          {isLoading ? (
            <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          )}
          Send
        </button>
      </div>
    </div>
  )
}
