import React from 'react'
import { ChatPanel } from './ChatPanel'
import { AgentsPanel } from './AgentsPanel'
import { PerfPanel } from './PerfPanel'
import { AppProviders } from '../AppProviders'

export const App: React.FC = () => {
  return (
    <AppProviders>
      <div className="min-h-screen">
        <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-900/80 backdrop-blur">
          <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
            <h1 className="text-lg font-semibold tracking-tight">l6e Forge: Workspace</h1>
            <PerfPanel />
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <section className="rounded-lg border border-slate-800 bg-slate-900 p-4">
            <h2 className="mb-2 text-slate-300 font-medium">Active Agents</h2>
            <AgentsPanel />
          </section>
          <section className="rounded-lg border border-slate-800 bg-slate-900 p-4 md:col-span-2">
            <h2 className="mb-2 text-slate-300 font-medium">Chat</h2>
            <ChatPanel />
          </section>
        </main>
      </div>
    </AppProviders>
  )
}


