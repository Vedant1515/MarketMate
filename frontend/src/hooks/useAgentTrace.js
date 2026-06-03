import { useState, useCallback } from 'react'

export function useAgentTrace() {
  const [traceSteps, setTraceSteps] = useState([])
  const [isThinking, setIsThinking] = useState(false)
  const [currentTool, setCurrentTool] = useState(null)

  const addTraceStep = useCallback((step) => {
    setTraceSteps((prev) => [...prev, { ...step, id: Date.now() + Math.random() }])
    setCurrentTool(step.tool_name || null)
    setIsThinking(true)
  }, [])

  const clearTrace = useCallback(() => {
    setTraceSteps([])
    setIsThinking(false)
    setCurrentTool(null)
  }, [])

  const markDone = useCallback(() => {
    setIsThinking(false)
    setCurrentTool(null)
  }, [])

  return {
    traceSteps,
    isThinking,
    currentTool,
    addTraceStep,
    clearTrace,
    markDone,
  }
}
