import React from 'react'
import { useMonitor } from '../utils/useMonitor'

export const PerfPanel: React.FC = () => {
  const { perf } = useMonitor()
  if (!perf) return <div className="text-slate-400 text-sm">Loading…</div>
  return (
    <div className="text-slate-400 text-sm">Avg: {perf.avg_ms.toFixed(1)} ms • P95: {perf.p95_ms.toFixed(1)} ms • Count: {perf.count}</div>
  )
}


