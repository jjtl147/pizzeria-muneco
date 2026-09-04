import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import products from '../data/products'
import ProductCard from '../components/ProductCard'

function Catalogo() {
  return (
    <div>
      <h2 className="mb-4 text-center">Nuestro menú</h2>
      
      {/* Grid responsive configurado según los breakpoints de Bootstrap:
          - xs={1}: 1 columna en móviles pequeños (<576px)
          - sm={2}: 2 columnas en pantallas pequeñas (≥576px)
          - md={3}: 3 columnas en pantallas medianas (≥768px)
          - lg={4}: 4 columnas en pantallas grandes (≥992px)
          - g-4: espaciado vertical y horizontal uniforme entre columnas */}
      <Row xs={1} sm={2} md={3} lg={4} className="g-4">
        {products.map((producto) => (
          <Col key={producto.id}>
            <ProductCard
              id={producto.id}
              nombre={producto.nombre}
              descripcion={producto.descripcion}
              precio={producto.precio}
              imagen={producto.imagen}
            />
          </Col>
        ))}
      </Row>
    </div>
  )
}

export default Catalogo