import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useMonitor } from '../utils/useMonitor'
import { apiUrl } from '../utils/api'

export const ChatPanel: React.FC = () => {
  const { chats, sendChat } = useMonitor()
  const [input, setInput] = useState('')
  const [agentOptions, setAgentOptions] = useState<string[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [persistent, setPersistent] = useState<boolean>(true)
  const [conversationId, setConversationId] = useState<string>('')
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const r = await fetch(apiUrl('/api/agents'))
        const data = await r.json()
        const discovered: string[] = data?.discovered || []
        const active: string[] = (data?.active || []).map((a: any) => a.name)
        const opts = Array.from(new Set([...(active || []), ...(discovered || [])]))
        setAgentOptions(opts)
        if (!selectedAgent && opts.length > 0) setSelectedAgent(opts[0])
      } catch {}
    })()
  }, [selectedAgent])

  const grouped = useMemo(() => {
    const groups: Record<string, any[]> = {}
    for (const c of chats || []) {
      const id = c.conversation_id || 'local'
      if (!groups[id]) groups[id] = []
      groups[id].push(c)
    }
    return Object.entries(groups).sort((a, b) => {
      const at = new Date(a[1][a[1].length - 1]?.timestamp || 0).getTime()
      const bt = new Date(b[1][b[1].length - 1]?.timestamp || 0).getTime()
      return bt - at
    })
  }, [chats])

  const onSend = async () => {
    const text = input.trim()
    if (!text) return
    try {
      const body: any = { agent: selectedAgent || 'demo', message: text }
      if (persistent) {
        if (!conversationId) {
          // seed a new conversation id on first send
          const seed = `${selectedAgent || 'demo'}:${Date.now().toString(36)}`
          setConversationId(seed)
          body.conversation_id = seed
        } else {
          body.conversation_id = conversationId
        }
      }
      const resp = await fetch(apiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (resp.ok) {
        const data = await resp.json()
        if (persistent && data?.conversation_id) setConversationId(data.conversation_id)
      }
    } catch {}
    setInput('')
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div>
      <div className="font-mono text-xs">
        {grouped.map(([id, items]) => (
          <div className="mb-3" key={id}>
            <div className="text-xs text-slate-400 mt-2 mb-1 border-t border-dashed border-slate-800 pt-2 flex items-center justify-between">
              <span className="font-semibold">{id}</span>
              <span className="text-slate-500">{(items as any[]).length} msgs</span>
            </div>
            {(items as any[]).map((c: any, idx: number) => (
              <div key={idx} className="border-b border-dashed border-slate-800 py-1">
                <span className="text-slate-500">{new Date(c.timestamp).toLocaleTimeString()}</span> <strong>[{c.role}]</strong> {c.content}
              </div>
            ))}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <div className="mt-2 flex gap-2">
        <select className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1" value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)}>
          {agentOptions.map(a => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <label className="flex items-center gap-1 text-slate-400 text-sm">
          <input type="checkbox" className="accent-emerald-500" checked={persistent} onChange={e => setPersistent(e.target.checked)} /> persistent
        </label>
        {persistent && conversationId && (
          <span className="text-slate-500 text-xs">conv: {conversationId}</span>
        )}
        <input className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={input} onChange={e => setInput(e.target.value)} placeholder="Say something…" onKeyDown={e => { if (e.key === 'Enter') onSend() }} />
        <button className="rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 px-3 py-2" onClick={async () => { const text = input.trim(); if (!text) return; await sendChat(text); setInput(''); }}>Log</button>
        <button className="rounded-md border border-emerald-600 bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-2" onClick={onSend}>Send via API</button>
      </div>
    </div>
  )
}


