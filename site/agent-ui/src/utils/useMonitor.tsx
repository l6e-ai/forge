import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'

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

  const refresh = useCallback(async () => {
    const [a, p, c] = await Promise.all([
      fetch('/monitor/api/agents').then(r => r.json()),
      fetch('/monitor/api/perf').then(r => r.json()),
      fetch('/monitor/api/chats').then(r => r.json()),
    ])
    setAgents(a)
    setPerf(p)
    setChats(c)
  }, [])

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

      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${proto}://${location.host}/monitor/ws`)
      wsRef.current = ws

      ws.onopen = () => {
        // reset backoff on successful connect
        reconnectDelayMs = 500
      }

      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data)
          if (msg.type === 'snapshot') {
            setAgents(msg.agents)
            setPerf(msg.perf)
            return
          }
          if (msg.type === 'metric' && msg.data?.name === 'response_time_ms') {
            fetch('/monitor/api/perf').then(r => r.json()).then(setPerf)
          }
          if (msg.type === 'event') {
            const et = msg.data?.event_type
            if (et === 'chat.message') {
              fetch('/monitor/api/chats').then(r => r.json()).then(setChats)
            }
            if (et === 'agent.registered' || et === 'agent.unregistered') {
              fetch('/monitor/api/agents').then(r => r.json()).then(setAgents)
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
    await fetch('/monitor/api/ingest/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: 'user', content: text, conversation_id: 'local' })
    })
  }, [])

  const value = useMemo(() => ({ agents, perf, chats, sendChat }), [agents, perf, chats, sendChat])
  return <MonitorContext.Provider value={value}>{children}</MonitorContext.Provider>
}

export const useMonitor = () => React.useContext(MonitorContext)


