const API_BASE_ENV = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

// API base (FastAPI)
export const API_BASE: string = (() => {
  return API_BASE_ENV.replace(/\/$/, '')
})()

export const apiUrl = (path: string) => `${API_BASE}${path.startsWith('/') ? path : '/' + path}`

// Build WebSocket URL from API base (supports absolute or relative VITE_API_BASE)
export const apiWsUrl = (path: string) => {
  const ensureLeading = (p: string) => (p.startsWith('/') ? p : '/' + p)
  try {
    const base = API_BASE.startsWith('http') ? API_BASE : `${location.origin}${ensureLeading(API_BASE)}`
    const u = new URL(base)
    const proto = u.protocol === 'https:' ? 'wss:' : 'ws:'
    const basePath = u.pathname.endsWith('/') ? u.pathname.slice(0, -1) : u.pathname
    const tail = ensureLeading(path)
    return `${proto}//${u.host}${basePath}${tail}`
  } catch {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${location.host}${ensureLeading(API_BASE)}${ensureLeading(path)}`
  }
}
