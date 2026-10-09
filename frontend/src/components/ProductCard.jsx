import { useContext, useState } from 'react'
import { Card, Button, Form } from 'react-bootstrap'
import { CartContext } from '../context/CartContext'
import { dinero } from '../utils/formato'

export default function ProductCard({ variantes }) {
  const { agregarAlCarrito } = useContext(CartContext)
  const [seleccion, setSeleccion] = useState(variantes[0].id)
  const producto = variantes.find((p) => p.id === seleccion) || variantes[0]
  const inventario = Array.isArray(producto.inventario) ? producto.inventario[0] : producto.inventario
  const disponible = Boolean(inventario && inventario.stock_actual > 0)
  const [agregado, setAgregado] = useState(false)
  function agregar() {
    agregarAlCarrito({ id: producto.id, nombre: producto.nombre, tamano: producto.tamano,
      precio: Number(producto.precio), imagen: producto.imagen })
    setAgregado(true)
  }
  return <Card className="h-100 shadow-sm">
    <Card.Img variant="top" src={producto.imagen || 'https://placehold.co/400x300?text=Pizza'} alt={producto.nombre} />
    <Card.Body className="d-flex flex-column"><Card.Title>{producto.nombre}</Card.Title>
      <Card.Text className="flex-grow-1">{producto.descripcion}</Card.Text>
      {(variantes.length > 1 || producto.tamano) && <Form.Group className="mb-3" controlId={`tamano-${variantes[0].id}`}>
        <Form.Label>Tamaño</Form.Label><Form.Select value={producto.id} onChange={(e) => { setSeleccion(Number(e.target.value)); setAgregado(false) }}>
          {variantes.map((p) => <option key={p.id} value={p.id}>{p.tamano || 'Único'} — {dinero(p.precio)}</option>)}
        </Form.Select></Form.Group>}
      <strong className="mb-2">{dinero(producto.precio)}</strong>
      <Button disabled={!disponible} onClick={agregar}>{disponible ? 'Agregar al carrito' : 'Sin stock'}</Button>
      {agregado && <small className="text-success mt-2" role="status">Producto agregado.</small>}
    </Card.Body>
  </Card>
}
