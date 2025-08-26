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
    // Replace WS with periodic polling from API proxy
    let cancelled = false
    const intervalMs = 2000
    const tick = async () => {
      if (cancelled) return
      try {
        const now = Date.now()
        if (now - lastPerfFetchRef.current >= MIN_INTERVAL_MS) {
          lastPerfFetchRef.current = now
          const p = await fetch(apiUrl('/perf')).then(r => r.json())
          setIfChanged(perf, p, setPerf)
        }
        if (now - lastChatsFetchRef.current >= MIN_INTERVAL_MS) {
          lastChatsFetchRef.current = now
          const c = await fetch(apiUrl('/chats')).then(r => r.json())
          setIfChanged(chats, c, setChats)
        }
      } catch {}
    }
    const id = window.setInterval(tick, intervalMs)
    tick()
    return () => { cancelled = true; window.clearInterval(id) }
  }, [])

  const value = useMemo(() => ({ agents, perf, chats }), [agents, perf, chats])
  return <MonitorContext.Provider value={value}>{children}</MonitorContext.Provider>
}

export const useMonitor = () => React.useContext(MonitorContext)


