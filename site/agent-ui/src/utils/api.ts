export const getEnv = (key: string): string | undefined => {
  const v = (import.meta as any)?.env?.[key]
  if (typeof v === 'string' && v.length > 0) return v
  return undefined
}

// API base (FastAPI) and Monitor base (monitor service)
export const API_BASE: string = (() => {
  const fromEnv = getEnv('VITE_API_BASE') || getEnv('VITE_APP_API_BASE')
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  return ''
})()

export const MONITOR_BASE: string = (() => {
  const fromEnv = getEnv('VITE_MONITOR_BASE') || getEnv('VITE_APP_MONITOR_BASE')
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  return ''
})()

export const apiUrl = (path: string) => `${API_BASE}${path.startsWith('/') ? path : '/' + path}`
export const monitorUrl = (path: string) => `${MONITOR_BASE}${path.startsWith('/') ? path : '/' + path}`


