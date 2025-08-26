import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { apiUrl } from './api'

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

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const res = await fetch(apiUrl('/agents'))
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setDiscovered(data.discovered || [])
      setActive(data.active || [])
    } catch (e: any) {
      setError(e?.message || 'Failed to load agents')
    } finally {
      setIsLoading(false)
    }
  }, [])

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


