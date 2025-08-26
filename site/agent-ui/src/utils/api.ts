const API_BASE_ENV = import.meta.env.VITE_API_BASE || '/api'
const MONITOR_BASE_ENV = import.meta.env.VITE_MONITOR_BASE || '/monitor'

// API base (FastAPI) and Monitor base (monitor service)
export const API_BASE: string = (() => {
  return API_BASE_ENV.replace(/\/$/, '')
})()  

export const MONITOR_BASE: string = (() => {
  return MONITOR_BASE_ENV.replace(/\/$/, '')
})()

export const apiUrl = (path: string) => `${API_BASE}${path.startsWith('/') ? path : '/' + path}`
export const monitorUrl = (path: string) => `${MONITOR_BASE}${path.startsWith('/') ? path : '/' + path}`


