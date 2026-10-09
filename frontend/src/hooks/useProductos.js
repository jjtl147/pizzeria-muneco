import { useEffect, useState } from 'react'
import api from '../services/api'


// Home y Catálogo comparten la consulta y sus estados de carga.
export default function useProductos() {
  const [productos, setProductos] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    async function consultar() {
      try {
        const respuesta = await api.get('/api/productos', {
          signal: controller.signal,
          timeout: 10000,
        })
        if (respuesta.data.status !== 'success' || !Array.isArray(respuesta.data.data)) {
          throw new Error('Respuesta de catálogo inválida')
        }
        if (!controller.signal.aborted) setProductos(respuesta.data.data)
      } catch {
        if (!controller.signal.aborted) {
          setError('No se pudo cargar el menú. Verifica la conexión con el servidor e intenta nuevamente.')
        }
      } finally {
        if (!controller.signal.aborted) setCargando(false)
      }
    }

    consultar()
    return () => controller.abort()
  }, [intento])

  function reintentarCarga() {
    setCargando(true)
    setError(null)
    setIntento((actual) => actual + 1)
  }

  return { productos, cargando, error, reintentarCarga }
}
