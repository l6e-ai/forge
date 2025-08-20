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

  const refresh = useCallback(async () => {
    const [a, p, c] = await Promise.all([
      fetch('/api/agents').then(r => r.json()),
      fetch('/api/perf').then(r => r.json()),
      fetch('/api/chats').then(r => r.json()),
    ])
    setAgents(a)
    setPerf(p)
    setChats(c)
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${location.host}/ws`)
    wsRef.current = ws
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'snapshot') {
          setAgents(msg.agents)
          setPerf(msg.perf)
          return
        }
        if (msg.type === 'metric' && msg.data?.name === 'response_time_ms') {
          fetch('/api/perf').then(r => r.json()).then(setPerf)
        }
        if (msg.type === 'event') {
          const et = msg.data?.event_type
          if (et === 'chat.message') {
            fetch('/api/chats').then(r => r.json()).then(setChats)
          }
          if (et === 'agent.registered' || et === 'agent.unregistered') {
            fetch('/api/agents').then(r => r.json()).then(setAgents)
          }
        }
      } catch (e) {
        // ignore
      }
    }
    ws.onclose = () => {
      setTimeout(() => {
        // force reload to reconnect
        location.reload()
      }, 1000)
    }
    return () => ws.close()
  }, [])

  const sendChat = useCallback(async (text: string) => {
    await fetch('/ingest/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: 'user', content: text, conversation_id: 'local' })
    })
  }, [])

  const value = useMemo(() => ({ agents, perf, chats, sendChat }), [agents, perf, chats, sendChat])
  return <MonitorContext.Provider value={value}>{children}</MonitorContext.Provider>
}

export const useMonitor = () => React.useContext(MonitorContext)


