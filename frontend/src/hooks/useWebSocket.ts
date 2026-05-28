import { useEffect, useRef, useCallback, useState } from 'react'
import type { WSEvent } from '@/types'

interface UseWebSocketOptions {
  channel?: string
  onEvent?: (event: WSEvent) => void
}

export function useWebSocket({ channel = 'global', onEvent }: UseWebSocketOptions = {}) {
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [events, setEvents] = useState<WSEvent[]>([])
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws?channel=${encodeURIComponent(channel)}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
    }

    ws.onmessage = (ev) => {
      try {
        const event: WSEvent = JSON.parse(ev.data)
        if (event.type === 'connected') return
        setEvents((prev) => [...prev.slice(-499), event])
        onEvent?.(event)
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectTimer.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [channel, onEvent])

  useEffect(() => {
    connect()
    const ping = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping')
      }
    }, 25000)
    return () => {
      clearInterval(ping)
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  const clearEvents = useCallback(() => setEvents([]), [])

  return { connected, events, clearEvents }
}
