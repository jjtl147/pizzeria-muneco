import { useCallback, useEffect, useState } from 'react'
import api, { guardarToken, leerToken, mensajeError } from '../services/api'
import { AuthContext } from './AuthContext'

export default function AuthProvider({ children }) {
  const [token, setToken] = useState(leerToken)
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(Boolean(token))
  const [errorSesion, setErrorSesion] = useState('')

  const cerrarSesion = useCallback(() => {
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
    window.addEventListener('sesion-expirada', cerrarSesion)
    return () => window.removeEventListener('sesion-expirada', cerrarSesion)
  }, [cerrarSesion])

  async function iniciarSesion(email, password) {
    const { data } = await api.post('/api/auth/login', { email, password })
    guardarToken(data.token)
    setToken(data.token)
    setUsuario(data.usuario)
    setErrorSesion('')
    setCargando(false)
    return data.usuario
  }

  const tieneRol = (...roles) => Boolean(usuario?.roles?.some((rol) => roles.includes(rol)))
  return <AuthContext.Provider value={{ usuario, cargando, errorSesion, iniciarSesion, cerrarSesion, tieneRol }}>
    {children}
  </AuthContext.Provider>
}
