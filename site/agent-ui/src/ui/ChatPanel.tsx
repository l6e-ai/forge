import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useMonitor } from '../utils/useMonitor'

export const ChatPanel: React.FC = () => {
  const { chats, sendChat } = useMonitor()
  const [input, setInput] = useState('')
  const [agentOptions, setAgentOptions] = useState<string[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const r = await fetch('/api/agents')
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
      await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent: selectedAgent || 'demo', message: text })
      })
    } catch {}
    setInput('')
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div>
      <div className="chat-logs">
        {grouped.map(([id, items]) => (
          <div className="conversation" key={id}>
            <div className="conv-header"><span className="conv-title">{id}</span><span className="muted">{(items as any[]).length} msgs</span></div>
            {(items as any[]).map((c: any, idx: number) => (
              <div key={idx} className="log"><span className="muted">{new Date(c.timestamp).toLocaleTimeString()}</span> <strong>[{c.role}]</strong> {c.content}</div>
            ))}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <div className="chat-input">
        <select value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)} style={{ marginRight: 8 }}>
          {agentOptions.map(a => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Say something…" onKeyDown={e => { if (e.key === 'Enter') onSend() }} />
        <button onClick={async () => { const text = input.trim(); if (!text) return; await sendChat(text); setInput(''); }}>Log</button>
        <button onClick={onSend}>Send via API</button>
      </div>
    </div>
  )
}


