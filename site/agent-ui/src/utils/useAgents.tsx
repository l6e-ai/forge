import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { apiUrl } from './api'
import { useMonitor } from './useMonitor'

export type ActiveAgent = { agent_id: string; name: string }

type AgentsState = {
  discovered: string[]
  active: ActiveAgent[]
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
  startAgent: (name: string) => Promise<void>
  stopAgent: (agentId: string) => Promise<void>
  agentNames: string[]
}

const AgentsContext = React.createContext<AgentsState>({
  discovered: [],
  active: [],
  isLoading: false,
  error: null,
  refresh: async () => {},
  startAgent: async () => {},
  stopAgent: async () => {},
  agentNames: [],
})

export const AgentsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [discovered, setDiscovered] = useState<string[]>([])
  const [active, setActive] = useState<ActiveAgent[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const didInitialRef = useRef(false)
  const { agents: monitorAgents } = useMonitor()

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const res = await fetch(apiUrl('/agents'))
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setDiscovered(data.discovered || [])
      // Prefer monitor-provided active agents; fall back to API response if not yet available
      if (!monitorAgents || monitorAgents.length === 0) {
        setActive(data.active || [])
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load agents')
    } finally {
      setIsLoading(false)
    }
  }, [monitorAgents])

  const startAgent = useCallback(async (name: string) => {
    await fetch(apiUrl('/agents/start'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    await refresh()
  }, [refresh])

  const stopAgent = useCallback(async (agentId: string) => {
    await fetch(apiUrl('/agents/stop'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: agentId }),
    })
    await refresh()
  }, [refresh])

  useEffect(() => {
    if (didInitialRef.current) return
    didInitialRef.current = true
    refresh()
  }, [refresh])

  // Keep active agents in sync with MonitorProvider websocket snapshot/events
  useEffect(() => {
    try {
      const mapped = (monitorAgents || []).map(a => ({ agent_id: a.agent_id, name: a.name }))
      // Only update if changed to avoid renders
      const prev = JSON.stringify(active)
      const next = JSON.stringify(mapped)
      if (prev !== next) setActive(mapped)
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monitorAgents])

  const agentNames = useMemo(() => {
    const activeNames = new Set((active || []).map(a => a.name))
    const all = new Set<string>([...Array.from(activeNames), ...discovered])
    return Array.from(all)
  }, [active, discovered])


  const value = useMemo<AgentsState>(() => ({
    discovered,
    active,
    isLoading,
    error,
    refresh,
    startAgent,
    stopAgent,
    agentNames,
  }), [discovered, active, isLoading, error, refresh, startAgent, stopAgent, agentNames])

  return <AgentsContext.Provider value={value}>{children}</AgentsContext.Provider>
}

export const useAgents = () => React.useContext(AgentsContext)


