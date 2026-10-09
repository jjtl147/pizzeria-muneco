import axios from 'axios'

export const TOKEN_KEY = 'muneco_token'
export function leerToken() {
  try { return sessionStorage.getItem(TOKEN_KEY) } catch { return null }
}
export function guardarToken(token) {
  if (token) sessionStorage.setItem(TOKEN_KEY, token)
  else sessionStorage.removeItem(TOKEN_KEY)
}

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || 'http://localhost:5000').replace(/\/$/, ''),
  timeout: 15000,
})
api.interceptors.request.use((config) => {
  const token = leerToken()
  if (token && !config.url.startsWith('/api/auth/login') && !config.url.startsWith('/api/auth/registro')) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
api.interceptors.response.use((respuesta) => respuesta, (error) => {
  if (error.response?.status === 401 && error.config?.headers?.Authorization === `Bearer ${leerToken()}`) {
    window.dispatchEvent(new CustomEvent('sesion-expirada'))
  }
  if (error.response?.status === 403) window.dispatchEvent(new Event('focus'))
  return Promise.reject(error)
})
export function mensajeError(error) {
  return error.response?.data?.mensaje || 'No se pudo conectar con el servidor. Intenta nuevamente.'
}
export default api
