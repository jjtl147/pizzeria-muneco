import { useEffect, useState } from 'react'
import api, { mensajeError } from '../services/api'

export default function useConsulta(ruta) {
  const [resultado, setResultado] = useState(null)
  const [version, setVersion] = useState(0)
  useEffect(() => {
    if (!ruta) return
    const controller = new AbortController()
    api.get(ruta, { signal: controller.signal }).then(({ data }) => {
      if (!controller.signal.aborted) setResultado({ ruta, version, datos: data, error: '' })
    }).catch((err) => {
      if (!controller.signal.aborted) setResultado({ ruta, version,
        datos: { data: [], hay_mas: false }, error: mensajeError(err) })
    })
    return () => controller.abort()
  }, [ruta, version])
  function recargar() { setVersion((v) => v + 1) }
  const vigente = ruta && resultado?.ruta === ruta && resultado.version === version
  return { ...(vigente ? resultado.datos : { data: [], hay_mas: false }),
    cargando: Boolean(ruta) && !vigente, error: vigente ? resultado.error : '', recargar }
}
