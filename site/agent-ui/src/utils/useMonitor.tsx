import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { monitorUrl, MONITOR_BASE } from './api'

type AgentStatus = { agent_id: string; name: string; status: string }
type Perf = { avg_ms: number; p95_ms: number; count: number }
type ChatLog = { conversation_id?: string; role: string; content: string; timestamp: string; agent_id?: string }

type MonitorState = {
  agents: AgentStatus[] | null
  perf: Perf | null
  chats: ChatLog[] | null
  sendChat: (text: string) => Promise<void>
}

const MonitorContext = React.createContext<MonitorState>({
  agents: null,
  perf: null,
  chats: null,
  sendChat: async () => {},
})

export const MonitorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [agents, setAgents] = useState<AgentStatus[] | null>(null)
  const [perf, setPerf] = useState<Perf | null>(null)
  const [chats, setChats] = useState<ChatLog[] | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
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

  const refresh = useCallback(async () => {
    const [a, p, c] = await Promise.all([
      fetch(monitorUrl('/api/agents')).then(r => r.json()),
      fetch(monitorUrl('/api/perf')).then(r => r.json()),
      fetch(monitorUrl('/api/chats')).then(r => r.json()),
    ])
    setIfChanged(agents, a, setAgents)
    setIfChanged(perf, p, setPerf)
    setIfChanged(chats, c, setChats)
  }, [agents, perf, chats])

  useEffect(() => {
    // Guard against React.StrictMode double-invocation in dev
    if (didInitialRefreshRef.current) return
    didInitialRefreshRef.current = true
    refresh()
  }, [refresh])

  useEffect(() => {
    let shouldReconnect = true
    let reconnectDelayMs = 500

    const connect = () => {
      if (!shouldReconnect) return
      // Avoid opening a second connection
      if (wsRef.current && wsRef.current.readyState < 2) return

      const base = MONITOR_BASE || ''
      let wsUrl: string
      if (base) {
        // If MONITOR_BASE is absolute (http/https), convert to ws/wss
        try {
          const u = new URL(base)
          u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
          u.pathname = (u.pathname.replace(/\/$/, '')) + '/ws'
          wsUrl = u.toString()
        } catch {
          // Fallback to relative
          wsUrl = '/monitor/ws'
        }
      } else {
        const proto = location.protocol === 'https:' ? 'wss' : 'ws'
        wsUrl = `${proto}://${location.host}/monitor/ws`
      }
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        // reset backoff on successful connect
        reconnectDelayMs = 500
      }

      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data)
          if (msg.type === 'snapshot') {
            setIfChanged(agents, msg.agents, setAgents)
            setIfChanged(perf, msg.perf, setPerf)
            return
          }
          if (msg.type === 'metric' && msg.data?.name === 'response_time_ms') {
            const now = Date.now()
            if (now - lastPerfFetchRef.current < MIN_INTERVAL_MS) return
            lastPerfFetchRef.current = now
            if (perfTimerRef.current) window.clearTimeout(perfTimerRef.current)
            perfTimerRef.current = window.setTimeout(() => {
              fetch(monitorUrl('/api/perf')).then(r => r.json()).then((p) => setIfChanged(perf, p, setPerf))
            }, 200)
          }
          if (msg.type === 'event') {
            const et = msg.data?.event_type
            if (et === 'chat.message') {
              const now = Date.now()
              if (now - lastChatsFetchRef.current < MIN_INTERVAL_MS) return
              lastChatsFetchRef.current = now
              if (chatsTimerRef.current) window.clearTimeout(chatsTimerRef.current)
              chatsTimerRef.current = window.setTimeout(() => {
                fetch('/monitor/api/chats').then(r => r.json()).then((c) => setIfChanged(chats, c, setChats))
              }, 200)
            }
            if (et === 'agent.registered' || et === 'agent.unregistered') {
              const now = Date.now()
              if (now - lastAgentsFetchRef.current < MIN_INTERVAL_MS) return
              lastAgentsFetchRef.current = now
              if (agentsTimerRef.current) window.clearTimeout(agentsTimerRef.current)
              agentsTimerRef.current = window.setTimeout(() => {
                fetch(monitorUrl('/api/agents')).then(r => r.json()).then((a) => setIfChanged(agents, a, setAgents))
              }, 200)
            }
          }
        } catch {
          // ignore
        }
      }

      ws.onclose = () => {
        if (!shouldReconnect) return
        setTimeout(() => {
          // Exponential backoff up to 10s
          reconnectDelayMs = Math.min(reconnectDelayMs * 2, 10_000)
          connect()
        }, reconnectDelayMs)
      }
    }

    connect()
    return () => {
      shouldReconnect = false
      try { wsRef.current?.close() } catch {}
      wsRef.current = null
    }
  }, [])

  const sendChat = useCallback(async (text: string) => {
    await fetch(monitorUrl('/ingest/chat'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: 'user', content: text, conversation_id: 'local' })
    })
  }, [])

  const value = useMemo(() => ({ agents, perf, chats, sendChat }), [agents, perf, chats, sendChat])
  return <MonitorContext.Provider value={value}>{children}</MonitorContext.Provider>
}

export const useMonitor = () => React.useContext(MonitorContext)


