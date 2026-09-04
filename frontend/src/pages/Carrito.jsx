import { useContext } from 'react'
import { CartContext } from '../context/CartContext'
import CarritoVista  from '../components/CarritoVista'

function Carrito() {
  const { items, eliminarDelCarrito, cambiarCantidad, totalPrecio} = useContext(CartContext)
return (
  <CarritoVista
  items={items}
  eliminarDelCarrito={eliminarDelCarrito}
  cambiarCantidad={cambiarCantidad}
  totalPrecio={totalPrecio}/>)
          }
export default Carrito