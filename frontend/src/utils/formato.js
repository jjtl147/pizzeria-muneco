export const dinero = (valor) => `$${Number(valor || 0).toFixed(2)}`
export const fecha = (valor) => new Date(valor).toLocaleString('es-BO', { timeZone: 'America/La_Paz' })
export const nombreProducto = (p) => `${p.nombre || p.nombre_producto || 'Producto'}${p.tamano ? ` (${p.tamano})` : ''}`
export function agruparProductos(productos) {
  const grupos = new Map()
  for (const p of productos) {
    const clave = p.tamano ? `${p.categoria_id}:${p.nombre}` : `id:${p.id}`
    if (!grupos.has(clave)) grupos.set(clave, [])
    grupos.get(clave).push(p)
  }
  return [...grupos.values()]
}
