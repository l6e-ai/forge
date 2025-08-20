import React from 'react'
import { useMonitor } from '../utils/useMonitor'

export const AgentsPanel: React.FC = () => {
  const { agents } = useMonitor()
  return (
    <div className="agents-list">
      {(agents || []).map(a => (
        <div key={a.agent_id} className="agent">
          <div className="flex">
            <strong>{a.name}</strong>
            <span className="muted">{a.agent_id.slice(0, 8)}</span>
          </div>
          <span className={`status ${a.status}`}>{a.status}</span>
        </div>
      ))}
    </div>
  )
}


