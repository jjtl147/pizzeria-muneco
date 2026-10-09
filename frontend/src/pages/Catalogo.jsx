import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import Spinner from 'react-bootstrap/Spinner'
import Alert from 'react-bootstrap/Alert'
import Button from 'react-bootstrap/Button'
import useProductos from '../hooks/useProductos'
import ProductCard from '../components/ProductCard'
import { agruparProductos } from '../utils/formato'

function Catalogo() {
  const { productos, cargando, error, reintentarCarga } = useProductos()

  return (
    <div className="py-4">
      <h2 className="mb-4 text-center">Nuestro menú</h2>

      {/* 1. Estado de Carga (Spinner) */}
      {cargando && (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" role="status">
            <span className="visually-hidden">Cargando productos...</span>
          </Spinner>
          <p className="mt-3 text-muted">Cargando nuestro menú artesanal...</p>
        </div>
      )}

      {/* 2. Estado de Error */}
      {error && !cargando && (
        <Alert variant="danger" className="text-center my-4">
          <Alert.Heading>Error al cargar el menú</Alert.Heading>
          <p className="mb-3">{error}</p>
          <Button variant="outline-danger" size="sm" onClick={reintentarCarga}>
            Reintentar
          </Button>
        </Alert>
      )}

      {/* 3. Catálogo vacío */}
      {!cargando && !error && productos.length === 0 && (
        <Alert variant="info" className="text-center my-4">
          No hay productos disponibles en este momento. Vuelve a consultar más tarde.
        </Alert>
      )}

      {/* 4. Grid de Productos (cuando existen datos) */}
      {!cargando && !error && productos.length > 0 && (
        <Row xs={1} sm={2} md={3} lg={4} className="g-4">
          {agruparProductos(productos).map((variantes) => (
            <Col key={variantes[0].id}><ProductCard variantes={variantes} /></Col>
          ))}
        </Row>
      )}
    </div>
  )
}

export default Catalogo
