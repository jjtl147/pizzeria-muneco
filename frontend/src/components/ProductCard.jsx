import { useContext } from 'react'
import Card from 'react-bootstrap/Card'
import Button from 'react-bootstrap/Button'
import { CartContext } from '../context/CartContext'

function ProductCard({ id, nombre, descripcion, precio, imagen }) {
  const { agregarAlCarrito } = useContext(CartContext)

  return (
    <Card className="h-100 shadow-sm">
      <Card.Img variant="top" src={imagen} alt={nombre} />
      <Card.Body className="d-flex flex-column">
        <Card.Title className="fw-bold">{nombre}</Card.Title>
        <Card.Text className="text-muted flex-grow-1">
          {descripcion}
        </Card.Text>
        <div className="d-flex justify-content-between align-items-center mt-3">
          <span className="fs-5 fw-bold text-primary">
            ${Number(precio).toFixed(2)}
          </span>
          <Button
            variant="primary"
            onClick={() => agregarAlCarrito({ id, nombre, precio, imagen })}
          >
            Agregar
          </Button>
        </div>
      </Card.Body>
    </Card>
  )
}

export default ProductCard