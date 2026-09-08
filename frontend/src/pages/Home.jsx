import { Link } from 'react-router-dom'
import Button from 'react-bootstrap/Button'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import Card from 'react-bootstrap/Card'
import products from '../data/products'

function Home() {
  // Tomamos los primeros 3 productos como muestra para la sección de populares
  const productosPopulares = products.slice(0, 3)

  return (
    <div className="pb-5">
      {/* 1. Hero Section */}
      <section className="text-center py-5">
        <p className="text-muted text-uppercase fw-semibold mb-2">Sabor hecho en casa</p>
        <h1 className="display-4 fw-bold">Tu próxima pizza empieza aquí</h1>
        <p className="lead text-secondary">
          Explora nuestro menú y descubre opciones preparadas para compartir.
        </p>
        <Button as={Link} to="/catalogo" variant="primary" size="lg" className="mt-3">
          Ver catálogo
        </Button>
      </section>

      <hr className="my-5" />

      {/* 2. Sección "¿Cómo funciona?" */}
      <section className="my-5">
        <h2 className="text-center mb-4">¿Cómo funciona?</h2>
        <Row xs={1} md={3} className="g-4 text-center">
          <Col>
            <Card className="h-100 shadow-sm border-0 bg-light">
              <Card.Body className="p-4">
                <div className="fs-1 text-primary fw-bold mb-3">1</div>
                <Card.Title className="fw-bold">Elige tu pizza</Card.Title>
                <Card.Text className="text-muted">
                  Explora nuestro catálogo con variedad de sabores e ingredientes frescos.
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
          <Col>
            <Card className="h-100 shadow-sm border-0 bg-light">
              <Card.Body className="p-4">
                <div className="fs-1 text-primary fw-bold mb-3">2</div>
                <Card.Title className="fw-bold">Agrégala al carrito</Card.Title>
                <Card.Text className="text-muted">
                  Personaliza tu pedido y revisa el resumen de tu compra fácilmente.
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
          <Col>
            <Card className="h-100 shadow-sm border-0 bg-light">
              <Card.Body className="p-4">
                <div className="fs-1 text-primary fw-bold mb-3">3</div>
                <Card.Title className="fw-bold">Recíbela en tu puerta</Card.Title>
                <Card.Text className="text-muted">
                  Te la llevamos caliente y lista para disfrutar en pocos minutos.
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </section>

      <hr className="my-5" />

      {/* 3. Sección de Productos Populares (solo vitrina) */}
      <section className="my-5">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h2 className="mb-0">Pizzas populares</h2>
          <Button as={Link} to="/catalogo" variant="outline-primary" size="sm">
            Ver todas
          </Button>
        </div>
        <Row xs={1} md={3} className="g-4">
          {productosPopulares.map((producto) => (
            <Col key={producto.id}>
              <Card className="h-100 shadow-sm">
                <Card.Img variant="top" src={producto.imagen} alt={producto.nombre} />
                <Card.Body className="d-flex flex-column">
                  <Card.Title className="fw-bold">{producto.nombre}</Card.Title>
                  <Card.Text className="text-muted flex-grow-1">
                    {producto.descripcion}
                  </Card.Text>
                  <div className="mt-3">
                    <span className="fs-5 fw-bold text-primary">
                      ${Number(producto.precio).toFixed(2)}
                    </span>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      </section>
    </div>
  )
}

export default Home