import { useEffect, useState } from 'react'
import api, { mensajeError } from '../services/api'

export default function useConsulta(ruta) {
  const [resultado, setResultado] = useState({ data: [], hay_mas: false })
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [version, setVersion] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    api.get(ruta, { signal: controller.signal }).then(({ data }) => {
      if (!controller.signal.aborted) { setResultado(data); setError('') }
    }).catch((err) => { if (!controller.signal.aborted) setError(mensajeError(err)) })
      .finally(() => { if (!controller.signal.aborted) setCargando(false) })
    return () => controller.abort()
  }, [ruta, version])
  function recargar() { setCargando(true); setError(''); setVersion((v) => v + 1) }
  return { ...resultado, cargando, error, recargar }
}
