import React, { useEffect, useState } from 'react'
import { useMonitor } from '../utils/useMonitor'
import { apiUrl } from '../utils/api'

export const AgentsPanel: React.FC = () => {
  const { agents } = useMonitor()
  const [discovered, setDiscovered] = useState<string[]>([])
  const [active, setActive] = useState<{ agent_id: string; name: string }[]>([])

  useEffect(() => {
    ;(async () => {
      try {
        const res = await fetch(apiUrl('/api/agents'))
        console.log('res', res)
        const data = await res.json()
        setDiscovered(data.discovered || [])
        setActive(data.active || [])
      } catch {}
    })()
  }, [])

  const startAgent = async (name: string) => {
    await fetch(apiUrl('/api/agents/start'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })
    const res = await fetch(apiUrl('/api/agents'))
    const data = await res.json()
    setDiscovered(data.discovered || [])
    setActive(data.active || [])
  }

  const stopAgent = async (agent_id: string) => {
    await fetch(apiUrl('/api/agents/stop'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ agent_id }) })
    const res = await fetch(apiUrl('/api/agents'))
    const data = await res.json()
    setDiscovered(data.discovered || [])
    setActive(data.active || [])
  }

  const activeNames = new Set((active || []).map(a => a.name))
  const inactiveDiscovered = (discovered || []).filter(name => !activeNames.has(name))

  return (
    <div className="flex flex-col gap-2">
      {active.map(a => (
        <div key={a.agent_id} className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-950/40 px-3 py-2">
          <div className="flex items-center gap-2">
            <span className="font-medium">{a.name}</span>
            <span className="text-xs text-slate-400">{a.agent_id.slice(0, 8)}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs rounded-full border border-emerald-600/50 bg-emerald-600/10 text-emerald-400 px-2 py-0.5">active</span>
            <button className="text-xs rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 px-2 py-1" onClick={() => stopAgent(a.agent_id)}>Stop</button>
          </div>
        </div>
      ))}
      {inactiveDiscovered.map(name => (
        <div key={name} className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-950/40 px-3 py-2">
          <div className="flex items-center gap-2">
            <span className="font-medium">{name}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs rounded-full border border-rose-600/50 bg-rose-600/10 text-rose-400 px-2 py-0.5">inactive</span>
            <button className="text-xs rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 px-2 py-1" onClick={() => startAgent(name)}>Start</button>
          </div>
        </div>
      ))}
    </div>
  )
}


