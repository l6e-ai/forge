import React from 'react'
import { useAgents } from '../utils/useAgents'

export const AgentsPanel: React.FC = () => {
  const { discovered, active, startAgent, stopAgent } = useAgents()

  const onStart = async (name: string) => { await startAgent(name) }
  const onStop = async (agent_id: string) => { await stopAgent(agent_id) }

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
            <button className="text-xs rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 px-2 py-1" onClick={() => onStop(a.agent_id)}>Stop</button>
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
            <button className="text-xs rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 px-2 py-1" onClick={() => onStart(name)}>Start</button>
          </div>
        </div>
      ))}
    </div>
  )
}


