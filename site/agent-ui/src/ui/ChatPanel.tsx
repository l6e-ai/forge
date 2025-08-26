import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { useMonitor } from '../utils/useMonitor'
import { apiUrl } from '../utils/api'
import { useAgents } from '../utils/useAgents'

export const ChatPanel: React.FC = () => {
  const { chats } = useMonitor()
  const { agentNames } = useAgents()
  const [input, setInput] = useState('')
  const [agentOptions, setAgentOptions] = useState<string[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [persistent, setPersistent] = useState<boolean>(true)
  const [conversationId, setConversationId] = useState<string>('')
  const endRef = useRef<HTMLDivElement | null>(null)
  const [isSending, setIsSending] = useState(false)
  const reqSeqRef = useRef(0)
  const isSendingRef = useRef(false)
  const [sendingConvId, setSendingConvId] = useState<string | null>(null)

  // Loading status messages shown while awaiting a response
  const statusMessages = useMemo(() => (
    [
      'Thinking…',
      'Reasoning through memory…',
      'Analyzing context…',
      'Planning next steps…',
      'Drafting response…',
    ]
  ), [])
  const [statusIdx, setStatusIdx] = useState(0)

  useEffect(() => {
    if (!isSending) return
    setStatusIdx(0)
    const id = window.setInterval(() => {
      setStatusIdx(i => (i + 1) % statusMessages.length)
    }, 1200)
    return () => { window.clearInterval(id) }
  }, [isSending, statusMessages.length])

  const stableHash = (s: string) => {
    let h = 5381
    for (let i = 0; i < s.length; i++) {
      h = ((h << 5) + h) ^ s.charCodeAt(i)
    }
    return (h >>> 0).toString(36)
  }

  const seedConversationId = useCallback(() => {
    const agent = selectedAgent || 'demo'
    return `${agent}:${Date.now().toString(36)}`
  }, [selectedAgent])

  useEffect(() => {
    const opts = agentNames
    setAgentOptions(opts)
    if (!selectedAgent && opts.length > 0) setSelectedAgent(opts[0])
  }, [agentNames, selectedAgent])

  const grouped = useMemo(() => {
    const groups: Record<string, any[]> = {}
    for (const c of chats || []) {
      const id = c.conversation_id || 'local'
      if (!groups[id]) groups[id] = []
      groups[id].push(c)
    }
    const ordered = Object.entries(groups).sort((a, b) => {
      const at = new Date(a[1][a[1].length - 1]?.timestamp || 0).getTime()
      const bt = new Date(b[1][b[1].length - 1]?.timestamp || 0).getTime()
      return bt - at
    })
    return { groups, ordered }
  }, [chats])

  const activeConversationId = useMemo(() => {
    if (persistent && conversationId) return conversationId
    return grouped.ordered[0]?.[0] || ''
  }, [persistent, conversationId, grouped])

  const activeMessages = useMemo(() => grouped.groups[activeConversationId] || [], [grouped, activeConversationId])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeMessages.length])

  const onSend = async () => {
    console.log('onSend', isSendingRef.current)
    if (isSendingRef.current) return
    const text = input.trim()
    if (!text) return
    try {
      isSendingRef.current = true
      setIsSending(true)
      const body: any = { agent: selectedAgent || 'demo', message: text }
      let convForSend: string | null = null
      if (persistent) {
        if (!conversationId) {
          // seed a new conversation id on first send
          const seed = `${selectedAgent || 'demo'}:${Date.now().toString(36)}`
          setConversationId(seed)
          body.conversation_id = seed
          convForSend = seed
        } else {
          body.conversation_id = conversationId
          convForSend = conversationId
        }
      }
      if (convForSend) setSendingConvId(convForSend)
      const seq = ++reqSeqRef.current
      const request_id = `${body.conversation_id || 'local'}:${stableHash(text)}:${seq}`
      body.request_id = request_id
      const resp = await fetch(apiUrl('/chat'), {
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
    setIsSending(false)
    isSendingRef.current = false
    setSendingConvId(null)
  }

  // Monitor is read-only; all sends go through API

  return (
    <div>
      {/* Tabs: conversations */}
      <div className="mb-2 overflow-x-auto">
        <div className="flex items-center gap-2 min-w-max">
          {grouped.ordered.map(([id, items]) => {
            const active = id === activeConversationId
            const label = `${id}`
            return (
              <button
                key={id}
                title={label}
                onClick={() => { setConversationId(id); if (!persistent) setPersistent(true) }}
                className={`text-xs px-2 py-1 rounded-md border ${active ? 'border-emerald-600 bg-emerald-600/20 text-emerald-300' : 'border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-600'}`}
                role="tab"
                aria-selected={active}
              >
                {id}
                <span className="ml-1 text-slate-500">· {(items as any[]).length}</span>
              </button>
            )
          })}
          <button
            onClick={() => { const seed = seedConversationId(); setPersistent(true); setConversationId(seed) }}
            className="text-xs px-2 py-1 rounded-md border border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-600"
          >
            + New
          </button>
        </div>
      </div>

      {/* Messages list */}
      <div className="rounded-md border border-slate-800 bg-slate-950/40 p-3 h-[55vh] overflow-y-auto">
        {activeMessages.map((c: any, idx: number) => {
          const isUser = c.role === 'user'
          return (
            <div key={idx} className={`mb-3 flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div className={`${isUser ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-100'} max-w-[80%] rounded-2xl px-3 py-2 shadow-sm`}>
                <div className="text-[10px] opacity-70 mb-1">
                  {new Date(c.timestamp).toLocaleTimeString()} · {isUser ? 'you' : 'assistant'}
                </div>
                <div className="whitespace-pre-wrap break-words">
                  {c.content}
                </div>
              </div>
            </div>
          )
        })}
        {/* Loading bubble */}
        {isSending && sendingConvId === activeConversationId && (
          <div className="mb-3 flex justify-start" aria-live="polite" aria-busy="true">
            <div className="bg-slate-800 text-slate-100 max-w-[80%] rounded-2xl px-3 py-2 shadow-sm">
              <div className="text-[10px] opacity-70 mb-1">thinking…</div>
              <div className="flex items-center gap-3">
                <div className="h-1.5 w-28 bg-slate-700 rounded overflow-hidden">
                  <div className="h-1.5 w-1/3 bg-emerald-500 animate-pulse rounded" />
                </div>
                <div className="text-xs text-slate-300 whitespace-nowrap">{statusMessages[statusIdx]}</div>
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Composer and dev controls */}
      <div className="mt-3">
        <div className="flex items-center gap-2 mb-2">
          <select className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1" value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)}>
            {agentOptions.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <label className="flex items-center gap-1 text-slate-400 text-sm">
            <input type="checkbox" className="accent-emerald-500" checked={persistent} onChange={e => setPersistent(e.target.checked)} /> persistent
          </label>
          {persistent && activeConversationId && (
            <span className="text-slate-500 text-xs">conv: {activeConversationId}</span>
          )}
          <button
            onClick={() => { const seed = seedConversationId(); setPersistent(true); setConversationId(seed) }}
            className="ml-auto text-xs px-2 py-1 rounded-md border border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-600"
          >New chat</button>
        </div>
        <div className="flex items-center gap-2">
          <input className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2" value={input} onChange={e => setInput(e.target.value)} placeholder="Say something…" onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.repeat) { e.preventDefault(); if (!isSendingRef.current) onSend() } }} />
          {/* Removed monitor send to avoid duplicate pathways */}
          <button className="rounded-md border border-emerald-600 bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-2 disabled:opacity-50" disabled={isSending} onClick={onSend}>Send via API</button>
        </div>
      </div>
    </div>
  )
}


