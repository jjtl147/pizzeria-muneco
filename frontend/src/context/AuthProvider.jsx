import { useCallback, useEffect, useState } from 'react'
import api, { guardarToken, guardarSesion, leerSesion, leerToken, mensajeError, renovarSesion } from '../services/api'
import { AuthContext } from './AuthContext'

export default function AuthProvider({ children }) {
  const [token, setToken] = useState(leerToken)
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(Boolean(token))
  const [errorSesion, setErrorSesion] = useState('')

  const cerrarSesion = useCallback(() => {
    const actual = leerToken()
    if (actual) api.post('/api/auth/logout', {}, { headers: { Authorization: `Bearer ${actual}` } }).catch(() => {})
    guardarToken(null)
    setToken(null)
    setUsuario(null)
    setCargando(false)
    setErrorSesion('')
    window.dispatchEvent(new CustomEvent('limpiar-carrito'))
  }, [])

  useEffect(() => {
    if (!token) return
    const controller = new AbortController()
    const comprobar = () => {
      api.get('/api/auth/perfil', { signal: controller.signal }).then(({ data }) => {
        if (!controller.signal.aborted && token === leerToken()) {
          setUsuario(data.usuario)
          setErrorSesion('')
        }
      }).catch((error) => {
        if (!controller.signal.aborted) setErrorSesion(mensajeError(error))
      }).finally(() => { if (!controller.signal.aborted) setCargando(false) })
    }
    comprobar()
    window.addEventListener('focus', comprobar)
    return () => { controller.abort(); window.removeEventListener('focus', comprobar) }
  }, [token])

  useEffect(() => {
    const actualizar = (e) => {
      setToken(e.detail.token)
      if (e.detail.usuario) setUsuario(e.detail.usuario)
    }
    window.addEventListener('sesion-expirada', cerrarSesion)
    window.addEventListener('sesion-actualizada', actualizar)
    const timer = window.setInterval(() => {
      const sesion = leerSesion()
      if (sesion?.expires_at <= Date.now() / 1000 + 60) renovarSesion().catch(() => {})
    }, 30000)
    return () => {
      window.removeEventListener('sesion-expirada', cerrarSesion)
      window.removeEventListener('sesion-actualizada', actualizar)
      window.clearInterval(timer)
    }
  }, [cerrarSesion])

  async function iniciarSesion(email, password) {
    const { data } = await api.post('/api/auth/login', { email, password })
    guardarSesion(data)
    setToken(data.token)
    setUsuario(data.usuario)
    setErrorSesion('')
    setCargando(false)
    return data.usuario
  }

  async function aceptarSesion(datos) {
    const { data } = await api.get('/api/auth/perfil', { headers: { Authorization: `Bearer ${datos.token}` } })
    guardarSesion({ ...datos, usuario: data.usuario })
    setUsuario(data.usuario)
    setToken(datos.token)
    setCargando(false)
    setErrorSesion('')
  }

  const tieneRol = (...roles) => Boolean(usuario?.roles?.some((rol) => roles.includes(rol)))
  return <AuthContext.Provider value={{ usuario, cargando, errorSesion, iniciarSesion, aceptarSesion, cerrarSesion, tieneRol }}>
    {children}
  </AuthContext.Provider>
}
