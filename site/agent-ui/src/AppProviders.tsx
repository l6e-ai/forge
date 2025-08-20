import React from 'react'
import { MonitorProvider } from './utils/useMonitor'

export const AppProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <MonitorProvider>
      {children}
    </MonitorProvider>
  )
}


