import { useState, useCallback, useRef, useEffect } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { streamChat } from '../services/api'
import { useAgentTrace } from './useAgentTrace'

const SESSION_KEY = 'marketmate_session_id'

function getOrCreateSessionId() {
  let sid = sessionStorage.getItem(SESSION_KEY)
  if (!sid) {
    sid = uuidv4()
    sessionStorage.setItem(SESSION_KEY, sid)
  }
  return sid
}

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentOrder, setCurrentOrder] = useState(null)
  const sessionId = useRef(getOrCreateSessionId())
  const cleanupRef = useRef(null)
  const streamingIdRef = useRef(null)

  const { traceSteps, isThinking, currentTool, addTraceStep, clearTrace, markDone } = useAgentTrace()

  const appendToken = useCallback((token) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === streamingIdRef.current
          ? { ...msg, content: msg.content + token }
          : msg
      )
    )
  }, [])

  const sendMessage = useCallback(
    (text) => {
      if (!text.trim() || isStreaming) return

      const userMsg = {
        id: uuidv4(),
        role: 'user',
        content: text.trim(),
        timestamp: Date.now(),
      }

      const assistantId = uuidv4()
      streamingIdRef.current = assistantId

      const assistantMsg = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        isStreaming: true,
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsStreaming(true)
      setCurrentOrder(null)
      clearTrace()

      const cleanup = streamChat(
        text.trim(),
        sessionId.current,
        (trace) => {
          addTraceStep(trace)
        },
        (token) => {
          appendToken(token)
        },
        (order) => {
          setCurrentOrder(order)
        },
        () => {
          setIsStreaming(false)
          markDone()
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId ? { ...msg, isStreaming: false } : msg
            )
          )
          streamingIdRef.current = null
        },
        (error) => {
          setIsStreaming(false)
          markDone()
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? {
                    ...msg,
                    content: `Error: ${error}`,
                    isStreaming: false,
                    isError: true,
                  }
                : msg
            )
          )
          streamingIdRef.current = null
        }
      )

      cleanupRef.current = cleanup
    },
    [isStreaming, addTraceStep, appendToken, clearTrace, markDone]
  )

  const clearChat = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current()
      cleanupRef.current = null
    }
    setMessages([])
    setIsStreaming(false)
    setCurrentOrder(null)
    clearTrace()
    streamingIdRef.current = null
  }, [clearTrace])

  useEffect(() => {
    return () => {
      if (cleanupRef.current) {
        cleanupRef.current()
      }
    }
  }, [])

  return {
    messages,
    isStreaming,
    sessionId: sessionId.current,
    traceSteps,
    isThinking,
    currentTool,
    currentOrder,
    sendMessage,
    clearChat,
  }
}
