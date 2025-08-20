import React, { useEffect, useState } from 'react'
import { useMonitor } from '../utils/useMonitor'

export const AgentsPanel: React.FC = () => {
  const { agents } = useMonitor()
  const [discovered, setDiscovered] = useState<string[]>([])
  const [active, setActive] = useState<{ agent_id: string; name: string }[]>([])

  useEffect(() => {
    ;(async () => {
      try {
        const res = await fetch('/api/agents')
        console.log('res', res)
        const data = await res.json()
        setDiscovered(data.discovered || [])
        setActive(data.active || [])
      } catch {}
    })()
  }, [])

  const startAgent = async (name: string) => {
    await fetch('/api/agents/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })
    const res = await fetch('/api/agents')
    const data = await res.json()
    setDiscovered(data.discovered || [])
    setActive(data.active || [])
  }

  const stopAgent = async (agent_id: string) => {
    await fetch('/api/agents/stop', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ agent_id }) })
    const res = await fetch('/api/agents')
    const data = await res.json()
    setDiscovered(data.discovered || [])
    setActive(data.active || [])
  }

  return (
    <div className="agents-list">
      {active.map(a => (
        <div key={a.agent_id} className="agent">
          <div className="flex">
            <strong>{a.name}</strong>
            <span className="muted">{a.agent_id.slice(0, 8)}</span>
          </div>
          <div className="flex">
            <span className={`status ready`}>active</span>
            <button onClick={() => stopAgent(a.agent_id)}>Stop</button>
          </div>
        </div>
      ))}
      {discovered.map(name => (
        <div key={name} className="agent">
          <div className="flex">
            <strong>{name}</strong>
          </div>
          <div className="flex">
            <span className={`status offline`}>inactive</span>
            <button onClick={() => startAgent(name)}>Start</button>
          </div>
        </div>
      ))}
    </div>
  )
}


