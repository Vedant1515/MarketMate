import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

/**
 * Stream a chat message using Server-Sent Events (EventSource).
 * Calls the provided callbacks as events arrive.
 *
 * @param {string} message
 * @param {string} sessionId
 * @param {(trace: object) => void} onTrace
 * @param {(token: string) => void} onToken
 * @param {(order: object) => void} onOrder
 * @param {() => void} onDone
 * @param {(error: string) => void} onError
 * @returns {() => void} cleanup function to close the EventSource
 */
export function streamChat(message, sessionId, onTrace, onToken, onOrder, onDone, onError) {
  const params = new URLSearchParams({
    message,
    session_id: sessionId,
  })

  const url = `${BASE_URL}/api/chat/stream?${params.toString()}`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data)
      const { event_type, data } = parsed

      switch (event_type) {
        case 'trace':
          onTrace(data)
          break
        case 'token':
          onToken(data.token || '')
          break
        case 'order':
          onOrder(data)
          break
        case 'done':
          onDone()
          eventSource.close()
          break
        case 'error':
          onError(data.message || 'Unknown error')
          eventSource.close()
          break
        default:
          break
      }
    } catch (err) {
      onError(`Failed to parse SSE event: ${err.message}`)
      eventSource.close()
    }
  }

  eventSource.onerror = (err) => {
    const errorMsg = eventSource.readyState === EventSource.CLOSED
      ? 'Connection closed by server'
      : 'EventSource connection error'
    onError(errorMsg)
    eventSource.close()
  }

  return () => {
    eventSource.close()
  }
}

/**
 * Send a chat message via POST (non-streaming).
 *
 * @param {string} message
 * @param {string} sessionId
 * @param {Array<{role: string, content: string}>} history
 * @returns {Promise<{response: string, session_id: string, agent_trace: Array}>}
 */
export async function postChat(message, sessionId, history = []) {
  try {
    const response = await apiClient.post('/api/chat', {
      message,
      session_id: sessionId,
      conversation_history: history,
    })
    return response.data
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    throw new Error(msg)
  }
}

/**
 * Fetch current runtime settings from the backend.
 * @returns {Promise<{demo_mode: boolean, model: string}>}
 */
export async function fetchSettings() {
  try {
    const response = await apiClient.get('/api/settings')
    return response.data
  } catch (err) {
    return { demo_mode: true, model: 'unknown' }
  }
}

/**
 * Toggle demo mode on the backend.
 * @param {boolean} enabled
 * @returns {Promise<{demo_mode: boolean}>}
 */
export async function setDemoMode(enabled) {
  try {
    const response = await apiClient.post('/api/settings/demo', { enabled })
    return response.data
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    throw new Error(msg)
  }
}

/**
 * Fetch list of tracked items.
 * @returns {Promise<Array<{item, unit, unit_price_aud, spoilage_days}>>}
 */
export async function fetchItems() {
  const response = await apiClient.get('/api/sales/items')
  return response.data
}

/**
 * Log daily sales records.
 * @param {Array<{item, quantity_sold, unit_price_aud, date?}>} records
 * @param {string} date YYYY-MM-DD
 */
export async function logDailySales(records, date) {
  const response = await apiClient.post('/api/sales/daily', { records, date })
  return response.data
}

/**
 * Get demand forecast for a specific item.
 * @param {string} itemName
 */
export async function getForecast(itemName) {
  const response = await apiClient.get(`/api/sales/forecast/${encodeURIComponent(itemName)}`)
  return response.data
}

/**
 * Get overall sales stats.
 */
export async function getSalesStats() {
  const response = await apiClient.get('/api/sales/stats')
  return response.data
}

export default apiClient
