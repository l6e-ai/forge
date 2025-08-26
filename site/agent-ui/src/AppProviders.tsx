import React from 'react'
import { MonitorProvider } from './utils/useMonitor'
import { AgentsProvider } from './utils/useAgents'

export const AppProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <MonitorProvider>
      <AgentsProvider>
        {children}
      </AgentsProvider>
    </MonitorProvider>
  )
}


