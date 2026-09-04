import Table from 'react-bootstrap/Table'
import Button from 'react-bootstrap/Button'
import Alert from 'react-bootstrap/Alert'

/**
 * Componente visual para la vista del carrito de compras.
 * Recibe el estado y funciones de manipulación del carrito vía props.
 * 
 * Props:
 * - items: Array de productos en el carrito ({ id, nombre, precio, cantidad })
 * - eliminarDelCarrito: Función para remover un producto por su id
 * - cambiarCantidad: Función para actualizar la cantidad (id, nuevaCantidad)
 * - totalPrecio: Monto total acumulado del carrito (number)
 */
function CarritoVista({ items = [], eliminarDelCarrito, cambiarCantidad, totalPrecio = 0 }) {
  // Estado cuando el carrito no contiene productos
  if (!items || items.length === 0) {
    return (
      <div className="py-4 text-center">
        <h2 className="mb-4">Tu carrito</h2>
        <Alert variant="info" className="d-inline-block px-5 py-3">
          Tu carrito está vacío
        </Alert>
      </div>
    )
  }

  // Vista con la tabla de productos y el resumen de compra
  return (
    <div className="py-4">
      <h2 className="mb-4">Tu carrito</h2>

      <Table striped bordered hover responsive className="align-middle">
        <thead className="table-light text-center">
          <tr>
            <th className="text-start">Producto</th>
            <th>Precio</th>
            <th>Cantidad</th>
            <th>Subtotal</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="text-center">
              <td className="text-start fw-semibold">{item.nombre}</td>
              <td>${Number(item.precio).toFixed(2)}</td>
              <td>
                <div className="d-flex justify-content-center align-items-center gap-2">
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={() => cambiarCantidad(item.id, item.cantidad - 1)}
                  >
                    -
                  </Button>
                  <span className="fw-bold px-2">{item.cantidad}</span>
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={() => cambiarCantidad(item.id, item.cantidad + 1)}
                  >
                    +
                  </Button>
                </div>
              </td>
              <td className="fw-semibold">
                ${(item.precio * item.cantidad).toFixed(2)}
              </td>
              <td>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => eliminarDelCarrito(item.id)}
                >
                  Eliminar
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <div className="d-flex justify-content-end align-items-center mt-4 p-3 bg-light rounded border">
        <h4 className="fw-bold mb-0 text-dark">
          Total: <span className="text-primary">${Number(totalPrecio).toFixed(2)}</span>
        </h4>
      </div>
    </div>
  )
}

export default CarritoVista