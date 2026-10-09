import { createContext, useEffect, useState } from 'react'

const CartContext = createContext()
const CLAVE_CARRITO = 'muneco_carrito'
function leerCarrito() {
  try {
    const items = JSON.parse(sessionStorage.getItem(CLAVE_CARRITO) || '[]')
    return Array.isArray(items) ? items.filter((p) => Number.isInteger(p.id) && Number.isInteger(p.cantidad)
      && p.cantidad > 0 && Number.isFinite(Number(p.precio)) && Number(p.precio) >= 0 && typeof p.nombre === 'string') : []
  } catch { return [] }
}
function CartProvider({ children }) {
  const [items, setItems] = useState(leerCarrito)
  useEffect(() => { try { sessionStorage.setItem(CLAVE_CARRITO, JSON.stringify(items)) } catch { /* El carrito sigue en memoria. */ } }, [items])
  useEffect(() => {
    const limpiar = () => setItems([])
    window.addEventListener('limpiar-carrito', limpiar)
    return () => window.removeEventListener('limpiar-carrito', limpiar)
  }, [])
  function agregarAlCarrito(producto) {
    setItems((actuales) => actuales.some((p) => p.id === producto.id)
      ? actuales.map((p) => p.id === producto.id ? { ...p, cantidad: p.cantidad + 1 } : p)
      : [...actuales, { ...producto, cantidad: 1 }])
  }
  function eliminarDelCarrito(id) { setItems((actuales) => actuales.filter((p) => p.id !== id)) }
  function cambiarCantidad(id, cantidad) {
    if (!Number.isInteger(cantidad) || cantidad < 1) return
    setItems((actuales) => actuales.map((p) => p.id === id ? { ...p, cantidad } : p))
  }
  function vaciarCarrito() { setItems([]) }
  const totalItems = items.reduce((total, p) => total + p.cantidad, 0)
  const totalPrecio = items.reduce((total, p) => total + Number(p.precio) * p.cantidad, 0)
  return <CartContext.Provider value={{ items, agregarAlCarrito, eliminarDelCarrito, cambiarCantidad,
    vaciarCarrito, totalItems, totalPrecio }}>{children}</CartContext.Provider>
}
export { CartContext, CartProvider }
