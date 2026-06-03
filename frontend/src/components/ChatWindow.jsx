import React, { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'
import AgentTrace from './AgentTrace'
import DemoChips from './DemoChips'
import { useChat } from '../hooks/useChat'

export default function ChatWindow({ demoMode = true }) {
  const {
    messages,
    isStreaming,
    sessionId,
    traceSteps,
    isThinking,
    currentTool,
    currentOrder,
    sendMessage,
    clearChat,
  } = useChat()

  const [input, setInput] = useState('')
  const [traceCollapsed, setTraceCollapsed] = useState(false)
  const [showChips, setShowChips] = useState(true)
  const [mobileShowTrace, setMobileShowTrace] = useState(false)

  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  function handleSend() {
    const text = input.trim()
    if (!text || isStreaming) return
    setInput('')
    setShowChips(false)
    sendMessage(text)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleDemoSelect(query) {
    setInput('')
    setShowChips(false)
    sendMessage(query)
  }

  // Pair each assistant message with its order
  // The order arrives after the last token, so attach it to the last assistant message
  const lastAssistantIdx = messages.reduce((acc, msg, i) => msg.role === 'assistant' ? i : acc, -1)

  return (
    <div className="flex h-full overflow-hidden">
      {/* Chat panel */}
      <div className="flex flex-col flex-1 min-w-0 border-r border-border">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
              <div className="w-12 h-12 rounded-xl bg-accent/20 border border-accent/30 flex items-center justify-center">
                <span className="text-accent text-xl font-bold font-mono">M</span>
              </div>
              <div>
                <p className="text-text-primary font-semibold">Ask MarketMate</p>
                <p className="text-text-secondary text-sm mt-1">
                  What should you order? What's in season? What do you do with leftover stock?
                </p>
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              order={i === lastAssistantIdx && !isStreaming ? currentOrder : null}
            />
          ))}

          <div ref={messagesEndRef} />
        </div>

        {/* Demo chips */}
        <DemoChips
          onSelect={handleDemoSelect}
          visible={showChips && messages.length === 0 && demoMode}
        />

        {/* Input bar */}
        <div className="border-t border-border px-4 py-3">
          <div className="flex gap-2 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isStreaming}
              placeholder={isStreaming ? 'Generating response...' : 'Ask about orders, stock, seasonality...'}
              rows={1}
              className="flex-1 resize-none bg-surface border border-border rounded-xl px-4 py-2.5 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-accent/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-sans"
              style={{ minHeight: '42px', maxHeight: '120px' }}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
              }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className="h-[42px] w-[42px] rounded-xl bg-accent text-white flex items-center justify-center flex-shrink-0 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent/90 transition-colors"
            >
              {isStreaming ? (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
          </div>
          <div className="flex items-center justify-between mt-2 px-1">
            <span className="text-xs text-text-secondary font-mono opacity-50">
              session: {sessionId.slice(0, 8)}
            </span>
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="text-xs text-text-secondary hover:text-text-primary transition-colors"
              >
                clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Agent trace panel - desktop */}
      <div className="hidden md:flex flex-col w-72 lg:w-80 flex-shrink-0 bg-surface">
        <AgentTrace
          traceSteps={traceSteps}
          isThinking={isThinking}
          currentTool={currentTool}
          collapsed={traceCollapsed}
          onToggle={() => setTraceCollapsed((v) => !v)}
        />
      </div>

      {/* Agent trace toggle - mobile */}
      <div className="md:hidden fixed bottom-20 right-4 z-10">
        <button
          onClick={() => setMobileShowTrace((v) => !v)}
          className="w-10 h-10 rounded-full bg-surface border border-border text-text-secondary flex items-center justify-center shadow-lg"
        >
          {isThinking ? (
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          ) : (
            <span className="text-xs font-mono">{traceSteps.length}</span>
          )}
        </button>
      </div>

      {/* Agent trace drawer - mobile */}
      {mobileShowTrace && (
        <div className="md:hidden fixed inset-0 bg-black/60 z-20 flex items-end" onClick={() => setMobileShowTrace(false)}>
          <div
            className="w-full bg-surface rounded-t-2xl border-t border-border max-h-[60vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-10 h-1 bg-border rounded-full mx-auto mt-3 mb-2" />
            <AgentTrace
              traceSteps={traceSteps}
              isThinking={isThinking}
              currentTool={currentTool}
              collapsed={false}
              onToggle={() => setMobileShowTrace(false)}
            />
          </div>
        </div>
      )}
    </div>
  )
}
