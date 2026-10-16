import axios from 'axios'

export const TOKEN_KEY = 'muneco_token'
const SESSION_KEY = 'muneco_sesion'
export function leerToken() {
  try { return sessionStorage.getItem(TOKEN_KEY) } catch { return null }
}
export function leerSesion() {
  try { return JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null') } catch { return null }
}
export function guardarSesion(datos) {
  if (!datos?.token || !datos?.refresh_token) throw new Error('La sesión recibida no es válida.')
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({
    token: datos.token, refresh_token: datos.refresh_token, expires_at: datos.expires_at,
  }))
  sessionStorage.setItem(TOKEN_KEY, datos.token)
  window.dispatchEvent(new CustomEvent('sesion-actualizada', { detail: datos }))
}
export function guardarToken(token) {
  if (token) sessionStorage.setItem(TOKEN_KEY, token)
  else {
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(SESSION_KEY)
  }
}

const baseURL = (import.meta.env.VITE_API_URL || 'http://localhost:5000').replace(/\/$/, '')
const api = axios.create({ baseURL, timeout: 20000 })
let renovando
export async function renovarSesion() {
  if (renovando) return renovando
  const anterior = leerSesion()
  if (!anterior?.refresh_token) throw new Error('Inicia sesión nuevamente.')
  renovando = axios.post(`${baseURL}/api/auth/renovar`, {
    refresh_token: anterior.refresh_token,
  }, { timeout: 20000 }).then(({ data }) => {
    // No restaurar una sesión cerrada o reemplazada mientras se renovaba.
    if (leerToken() !== anterior.token) throw new Error('La sesión cambió.')
    guardarSesion(data)
    return data.token
  }).catch((error) => {
    if (error.response?.status === 401 && leerToken() === anterior.token) {
      window.dispatchEvent(new Event('sesion-expirada'))
    }
    throw error
  }).finally(() => { renovando = null })
  return renovando
}
api.interceptors.request.use(async (config) => {
  if (config.url.startsWith('/api/auth/') && config.url !== '/api/auth/perfil') return config
  let token = leerToken()
  const sesion = leerSesion()
  if (!config.headers.Authorization && token && sesion?.expires_at <= Date.now() / 1000 + 30) token = await renovarSesion()
  if (token && !config.headers.Authorization) config.headers.Authorization = `Bearer ${token}`
  return config
})
api.interceptors.response.use((respuesta) => respuesta, async (error) => {
  const config = error.config
  const autenticada = config?.headers?.Authorization === `Bearer ${leerToken()}`
  if (error.response?.status === 401 && autenticada) {
    if (!config._reintentado && !config.url.startsWith('/api/auth/') && leerSesion()?.refresh_token) {
      config._reintentado = true
      const token = await renovarSesion()
      config.headers.Authorization = `Bearer ${token}`
      return api(config)
    }
    // Perfil también puede recibir un access token revocado/expirado antes de
    // su vencimiento local. Un único intento de renovación es suficiente.
    if (!config._reintentado && config.url === '/api/auth/perfil' && leerSesion()?.refresh_token) {
      config._reintentado = true
      config.headers.Authorization = `Bearer ${await renovarSesion()}`
      return api(config)
    }
    window.dispatchEvent(new Event('sesion-expirada'))
  }
  if (error.response?.status === 403) window.dispatchEvent(new Event('focus'))
  return Promise.reject(error)
})
export function mensajeError(error) {
  return error.response?.data?.mensaje || error.message || 'No se pudo conectar con el servidor. Intenta nuevamente.'
}
export default api
