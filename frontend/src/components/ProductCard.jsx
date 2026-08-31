import Card from 'react-bootstrap/Card'
import Button from 'react-bootstrap/Button'

/**
 * Componente reutilizable para mostrar la información individual de un producto.
 * 
 * Props recibidas:
 * - nombre: string con el nombre del producto
 * - descripcion: string con la descripción del producto
 * - precio: number con el precio del producto
 * - imagen: string con la URL de la imagen representativa
 */
function ProductCard({ nombre, descripcion, precio, imagen }) {
  return (
    // La clase "h-100" asegura que todas las tarjetas en la misma fila tengan la misma altura
    <Card className="h-100 shadow-sm">
      <Card.Img variant="top" src={imagen} alt={nombre} />
      <Card.Body className="d-flex flex-column">
        <Card.Title className="fw-bold">{nombre}</Card.Title>
        <Card.Text className="text-muted flex-grow-1">
          {descripcion}
        </Card.Text>
        <div className="d-flex justify-content-between align-items-center mt-3">
          <span className="fs-5 fw-bold text-primary">${Number(precio).toFixed(2)}</span>
          <Button variant="primary">Agregar</Button>
        </div>
      </Card.Body>
    </Card>
  )
}

export default ProductCard

