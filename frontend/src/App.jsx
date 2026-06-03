import React, { useEffect, useState, useCallback } from 'react'
import ChatWindow from './components/ChatWindow'
import SalesLogModal from './components/SalesLogModal'
import { fetchSettings, setDemoMode, getSalesStats } from './services/api'

function useLiveClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return now
}

function formatDate(d) {
  return d.toLocaleDateString('en-AU', {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'
  })
}

function formatTime(d) {
  return d.toLocaleTimeString('en-AU', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
  })
}

export default function App() {
  const [demoMode, setDemoModeState] = useState(true)
  const [toggling, setToggling] = useState(false)
  const [settingsLoaded, setSettingsLoaded] = useState(false)
  const [showSalesModal, setShowSalesModal] = useState(false)
  const now = useLiveClock()
  const [salesStats, setSalesStats] = useState(null)

  useEffect(() => {
    fetchSettings().then((s) => {
      setDemoModeState(s.demo_mode)
      setSettingsLoaded(true)
    })
    getSalesStats().then(setSalesStats).catch(() => {})
  }, [])

  const handleToggle = useCallback(async () => {
    if (toggling) return
    setToggling(true)
    const next = !demoMode
    try {
      const result = await setDemoMode(next)
      setDemoModeState(result.demo_mode)
    } catch {
      // revert on error
    } finally {
      setToggling(false)
    }
  }, [demoMode, toggling])

  const handleSalesSaved = useCallback((result) => {
    setSalesStats((prev) => prev ? {
      ...prev,
      weeks_of_data: result.total_weeks_of_data,
      documents_in_chromadb: result.documents_reindexed || prev.documents_in_chromadb,
    } : null)
  }, [])

  return (
    <div className="flex flex-col h-screen bg-background text-text-primary font-sans overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent/20 border border-accent/30 flex items-center justify-center">
            <span className="text-accent text-sm font-bold font-mono">M</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-text-primary leading-none">MarketMate</h1>
            <p className="text-xs text-text-secondary mt-0.5">
              AI Ordering Assistant
              {salesStats && (
                <span className="ml-2 text-text-secondary/60 font-mono">
                  {salesStats.weeks_of_data}w data
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Live clock - centre of header */}
        <div className="hidden md:flex flex-col items-center">
          <span className="text-sm font-mono font-semibold text-text-primary tracking-wide">
            {formatTime(now)}
          </span>
          <span className="text-xs font-mono text-text-secondary mt-0.5">
            {formatDate(now)}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Log Sales button */}
          <button
            onClick={() => setShowSalesModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-background text-xs text-text-secondary hover:text-text-primary hover:border-accent/40 transition-all font-mono"
            title="Log today's sales to improve AI predictions"
          >
            <span className="text-accent">+</span>
            Log Sales
          </button>

          {/* Mode toggle */}
          {settingsLoaded && (
            <div className="flex items-center gap-2">
              <span className={`text-xs font-mono transition-colors ${demoMode ? 'text-accent' : 'text-text-secondary'}`}>
                Demo
              </span>

              <button
                onClick={handleToggle}
                disabled={toggling}
                aria-label={demoMode ? 'Switch to Live AI mode' : 'Switch to Demo mode'}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full border transition-all duration-300 focus:outline-none
                  disabled:opacity-50 disabled:cursor-not-allowed
                  ${demoMode ? 'bg-accent/20 border-accent/40' : 'bg-blue-500/20 border-blue-400/40'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full transition-all duration-300 shadow-sm
                    ${demoMode ? 'translate-x-1 bg-accent' : 'translate-x-6 bg-blue-400'}
                    ${toggling ? 'animate-pulse' : ''}
                  `}
                />
              </button>

              <span className={`text-xs font-mono transition-colors ${!demoMode ? 'text-blue-400' : 'text-text-secondary'}`}>
                Live AI
              </span>

              <span className={`text-xs px-2 py-0.5 rounded border font-mono ${
                demoMode
                  ? 'border-accent/30 bg-accent/10 text-accent'
                  : 'border-blue-400/30 bg-blue-500/10 text-blue-400'
              }`}>
                {demoMode ? 'Demo' : 'API'}
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Live mode info banner */}
      {settingsLoaded && !demoMode && (
        <div className="px-4 py-2 bg-blue-500/10 border-b border-blue-400/20 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse flex-shrink-0" />
          <p className="text-xs text-blue-300">
            Live AI mode - using Claude API.
            {salesStats && (
              <span className="ml-2 text-blue-300/70">
                Knowledge base: <span className="text-blue-300">{salesStats.weeks_of_data} weeks</span> of data,
                <span className="text-blue-300 ml-1">{salesStats.documents_in_chromadb} documents</span> in ChromaDB.
                Log daily sales to improve forecasts.
              </span>
            )}
          </p>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <ChatWindow demoMode={demoMode} />
      </main>

      {/* Sales log modal */}
      {showSalesModal && (
        <SalesLogModal
          onClose={() => setShowSalesModal(false)}
          onSaved={handleSalesSaved}
        />
      )}
    </div>
  )
}
