import React, { useState } from 'react'

const TOOL_STYLES = {
  sales_retriever: {
    color: 'text-accent',
    bg: 'bg-green-900/30',
    border: 'border-green-700/50',
    label: 'Sales Memory',
    description: 'Querying historical sales data via RAG',
  },
  demand_forecaster: {
    color: 'text-cyan-400',
    bg: 'bg-cyan-900/30',
    border: 'border-cyan-700/50',
    label: 'Demand Forecast',
    description: 'Running statistical demand prediction model',
  },
  holiday_checker: {
    color: 'text-blue-400',
    bg: 'bg-blue-900/30',
    border: 'border-blue-700/50',
    label: 'Holiday Check',
    description: 'Checking VIC public holidays and Melbourne events',
  },
  spoilage_scorer: {
    color: 'text-warning',
    bg: 'bg-amber-900/30',
    border: 'border-amber-700/50',
    label: 'Spoilage Risk',
    description: 'Calculating spoilage risk and velocity',
  },
  order_generator: {
    color: 'text-purple-400',
    bg: 'bg-purple-900/30',
    border: 'border-purple-700/50',
    label: 'Order Generator',
    description: 'Generating structured order recommendation',
  },
}

function ToolBadge({ toolName, isRunning }) {
  const style = TOOL_STYLES[toolName] || {
    color: 'text-text-secondary',
    bg: 'bg-surface',
    border: 'border-border',
    label: toolName,
    description: 'Processing...',
  }

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${style.bg} ${style.border}`}>
      <span className={`font-mono text-xs font-semibold ${style.color}`}>
        {style.label}
      </span>
      {isRunning && (
        <span className="flex gap-0.5">
          <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
        </span>
      )}
    </div>
  )
}

function TraceStep({ step, isLast, isThinking }) {
  const [expanded, setExpanded] = useState(false)
  const style = TOOL_STYLES[step.tool_name] || {
    color: 'text-text-secondary',
    label: step.tool_name,
    description: '',
  }
  const isRunning = isLast && isThinking

  return (
    <div className="flex gap-2">
      <div className="flex flex-col items-center">
        <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${isRunning ? 'animate-pulse' : ''} ${style.color.replace('text-', 'bg-')}`} />
        {!isLast && <div className="w-px flex-1 bg-border mt-1" />}
      </div>

      <div className="pb-3 flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-xs font-semibold font-mono ${style.color}`}>
            {style.label}
          </span>
          {isRunning && (
            <span className="flex gap-0.5">
              {[0, 150, 300].map((delay) => (
                <span
                  key={delay}
                  className={`w-1 h-1 rounded-full animate-bounce ${style.color.replace('text-', 'bg-')}`}
                  style={{ animationDelay: `${delay}ms` }}
                />
              ))}
            </span>
          )}
          <span className="text-xs text-text-secondary ml-auto">
            {new Date(step.timestamp * 1000).toLocaleTimeString()}
          </span>
        </div>

        <p className="text-xs text-text-secondary truncate">{style.description}</p>

        {step.output && (
          <button
            onClick={() => setExpanded((e) => !e)}
            className="text-xs text-text-secondary hover:text-text-primary mt-1 transition-colors"
          >
            {expanded ? 'Hide output' : 'Show output'}
          </button>
        )}

        {expanded && step.output && (
          <div className="mt-1.5 p-2 rounded bg-background border border-border text-xs text-text-secondary font-mono whitespace-pre-wrap break-words max-h-32 overflow-y-auto">
            {step.output}
          </div>
        )}
      </div>
    </div>
  )
}

export default function AgentTrace({ traceSteps, isThinking, currentTool, collapsed, onToggle }) {
  const hasActivity = traceSteps.length > 0 || isThinking

  return (
    <div className="flex flex-col h-full">
      <div
        className="flex items-center justify-between px-4 py-3 border-b border-border cursor-pointer select-none"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-text-primary">Agent Trace</span>
          {isThinking && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-accent/20 text-accent font-mono animate-pulse">
              thinking
            </span>
          )}
          {!isThinking && traceSteps.length > 0 && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-surface text-text-secondary font-mono">
              {traceSteps.length} step{traceSteps.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <span className="text-text-secondary text-xs">{collapsed ? '+' : '-'}</span>
      </div>

      {!collapsed && (
        <div className="flex-1 overflow-y-auto p-4">
          {!hasActivity && (
            <div className="flex flex-col items-center justify-center h-24 gap-2 text-text-secondary">
              <div className="w-8 h-8 rounded-full border border-border flex items-center justify-center">
                <span className="text-lg">?</span>
              </div>
              <p className="text-xs text-center">Waiting for a query...</p>
              <p className="text-xs text-center opacity-60">Tool calls will appear here</p>
            </div>
          )}

          {hasActivity && (
            <div className="space-y-0">
              {traceSteps.map((step, i) => (
                <TraceStep
                  key={step.id || i}
                  step={step}
                  isLast={i === traceSteps.length - 1}
                  isThinking={isThinking}
                />
              ))}
              {isThinking && traceSteps.length === 0 && (
                <div className="flex items-center gap-2 text-xs text-text-secondary">
                  <span className="flex gap-0.5">
                    {[0, 150, 300].map((delay) => (
                      <span
                        key={delay}
                        className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce"
                        style={{ animationDelay: `${delay}ms` }}
                      />
                    ))}
                  </span>
                  <span>Routing query...</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
