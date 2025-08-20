import React from 'react'
import { ChatPanel } from './ChatPanel'
import { AgentsPanel } from './AgentsPanel'
import { PerfPanel } from './PerfPanel'
import { AppProviders } from '../AppProviders'

export const App: React.FC = () => {
  return (
    <AppProviders>
      <div className="app">
        <header className="header">
          <h1>l6e forge UI</h1>
          <PerfPanel />
        </header>
        <main className="grid">
          <section className="card">
            <h2 className="section-title">Active Agents</h2>
            <AgentsPanel />
          </section>
          <section className="card" style={{ gridColumn: '1 / -1' }}>
            <h2 className="section-title">Chat</h2>
            <ChatPanel />
          </section>
        </main>
      </div>
    </AppProviders>
  )
}


