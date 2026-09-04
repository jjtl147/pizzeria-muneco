import { createContext, useState } from 'react'

const CartContext = createContext()

function CartProvider({ children }) {
  const [items, setItems] = useState([])

  // Agrega un producto, o suma cantidad si ya existe
  function agregarAlCarrito(producto) {
    const existente = items.find((item) => item.id === producto.id)

    if (existente) {
      setItems(
        items.map((item) =>
          item.id === producto.id
            ? { ...item, cantidad: item.cantidad + 1 }
            : item
        )
      )
    } else {
      setItems([...items, { ...producto, cantidad: 1 }])
    }
  }

  // Elimina un producto completamente del carrito
  function eliminarDelCarrito(id) {
    setItems(items.filter((item) => item.id !== id))
  }

  // Cambia la cantidad manualmente (ej. desde botones +/-)
  function cambiarCantidad(id, nuevaCantidad) {
    if (nuevaCantidad < 1) return
    setItems(
      items.map((item) =>
        item.id === id ? { ...item, cantidad: nuevaCantidad } : item
      )
    )
  }

  // Total de items (para el contador del navbar)
  const totalItems = items.reduce((acc, item) => acc + item.cantidad, 0)

  // Total en dinero
  const totalPrecio = items.reduce(
    (acc, item) => acc + item.precio * item.cantidad,
    0
  )

  return (
    <CartContext.Provider
      value={{
        items,
        agregarAlCarrito,
        eliminarDelCarrito,
        cambiarCantidad,
        totalItems,
        totalPrecio
      }}
    >
      {children}
    </CartContext.Provider>
  )
}

export { CartContext, CartProvider }