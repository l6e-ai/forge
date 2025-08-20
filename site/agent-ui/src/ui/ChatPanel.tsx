import React, { useMemo, useRef, useState } from 'react'
import { useMonitor } from '../utils/useMonitor'

export const ChatPanel: React.FC = () => {
  const { chats, sendChat } = useMonitor()
  const [input, setInput] = useState('')
  const endRef = useRef<HTMLDivElement | null>(null)

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
    await sendChat(text)
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
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Say something…" onKeyDown={e => { if (e.key === 'Enter') onSend() }} />
        <button onClick={onSend}>Log</button>
        <button onClick={async () => { if (!input.trim()) return; const res = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ agent: 'test-auto', message: input }) }); const data = await res.json(); console.log('api/chat', data); setInput(''); }}>Send via API</button>
      </div>
    </div>
  )
}


