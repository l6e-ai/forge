import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { apiUrl } from './api'

type AgentStatus = { agent_id: string; name: string; status: string }
type Perf = { avg_ms: number; p95_ms: number; count: number }
type ChatLog = { conversation_id?: string; role: string; content: string; timestamp: string; agent_id?: string }

type MonitorState = {
  agents: AgentStatus[] | null
  perf: Perf | null
  chats: ChatLog[] | null
}

const MonitorContext = React.createContext<MonitorState>({
  agents: null,
  perf: null,
  chats: null,
})

export const MonitorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [agents, setAgents] = useState<AgentStatus[] | null>(null)
  const [perf, setPerf] = useState<Perf | null>(null)
  const [chats, setChats] = useState<ChatLog[] | null>(null)
  const didInitialRefreshRef = useRef(false)

  // Debounce/throttle helpers
  const agentsTimerRef = useRef<number | null>(null)
  const perfTimerRef = useRef<number | null>(null)
  const chatsTimerRef = useRef<number | null>(null)
  const lastAgentsFetchRef = useRef<number>(0)
  const lastPerfFetchRef = useRef<number>(0)
  const lastChatsFetchRef = useRef<number>(0)
  const MIN_INTERVAL_MS = 500

  const setIfChanged = <T,>(prev: T | null, next: T, setter: (v: T) => void) => {
    try {
      if (prev == null) { setter(next); return }
      const a = JSON.stringify(prev)
      const b = JSON.stringify(next)
      if (a !== b) setter(next)
    } catch {
      setter(next)
    }
  }

  useEffect(() => {
    // Connect to API WebSocket for live updates
    let ws: WebSocket | null = null
    let shouldReconnect = true
    let reconnectDelayMs = 500

    const connect = () => {
      if (!shouldReconnect) return
      if (ws && ws.readyState < 2) return
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const url = `${proto}://${location.host}/api/ws`
      ws = new WebSocket(url)
      ws.onopen = () => { reconnectDelayMs = 500 }
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data)
          if (msg.type === 'snapshot') {
            setIfChanged(agents, msg.agents, setAgents)
            setIfChanged(perf, msg.perf, setPerf)
            return
          }
          if (msg.type === 'metric' && (msg.data?.name === 'response_time_ms' || msg.data?.avg_ms != null)) {
            // Accept either broadcast metric or fallback payload
            const p = msg.data?.avg_ms != null ? { avg_ms: msg.data.avg_ms, p95_ms: msg.data.p95_ms, count: msg.data.count } : undefined
            if (p) setIfChanged(perf, p, setPerf)
          }
          if (msg.type === 'event') {
            const et = msg.data?.event_type
            if (et === 'chat.message') {
              // Fetch latest chats debounce
              const now = Date.now()
              if (now - lastChatsFetchRef.current < MIN_INTERVAL_MS) return
              lastChatsFetchRef.current = now
              if (chatsTimerRef.current) window.clearTimeout(chatsTimerRef.current)
              chatsTimerRef.current = window.setTimeout(async () => {
                const c = await fetch(apiUrl('/chats')).then(r => r.json())
                setIfChanged(chats, c, setChats)
              }, 150)
            }
            if (et === 'agent.registered' || et === 'agent.unregistered' || et === 'agent.status') {
              const now = Date.now()
              if (now - lastAgentsFetchRef.current < MIN_INTERVAL_MS) return
              lastAgentsFetchRef.current = now
              if (agentsTimerRef.current) window.clearTimeout(agentsTimerRef.current)
              agentsTimerRef.current = window.setTimeout(async () => {
                const a = await fetch(apiUrl('/agents')).then(r => r.json())
                setIfChanged(agents, a, setAgents)
              }, 150)
            }
          }
        } catch {}
      }
      ws.onclose = () => {
        if (!shouldReconnect) return
        setTimeout(() => { reconnectDelayMs = Math.min(reconnectDelayMs * 2, 10000); connect() }, reconnectDelayMs)
      }
    }

    connect()
    return () => { shouldReconnect = false; try { ws?.close() } catch {} ws = null }
  }, [])

  const value = useMemo(() => ({ agents, perf, chats }), [agents, perf, chats])
  return <MonitorContext.Provider value={value}>{children}</MonitorContext.Provider>
}

export const useMonitor = () => React.useContext(MonitorContext)


