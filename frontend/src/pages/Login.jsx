import { Link } from 'react-router-dom'
import Card from 'react-bootstrap/Card'
import Form from 'react-bootstrap/Form'
import Button from 'react-bootstrap/Button'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'

function Login() {
  const handleSubmit = (e) => {
    e.preventDefault()
    // Aquí se conectará la autenticación con el backend
  }

  return (
    <Row className="justify-content-center align-items-center py-5">
      <Col xs={12} sm={10} md={8} lg={5} xl={4}>
        <Card className="shadow-sm">
          <Card.Body className="p-4">
            <h2 className="text-center mb-4 fw-bold">Iniciar sesión</h2>
            
            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3" controlId="loginEmail">
                <Form.Label>Correo electrónico</Form.Label>
                <Form.Control
                  type="email"
                  placeholder="ejemplo@correo.com"
                />
              </Form.Group>

              <Form.Group className="mb-4" controlId="loginPassword">
                <Form.Label>Contraseña</Form.Label>
                <Form.Control
                  type="password"
                  placeholder="Tu contraseña"
                />
              </Form.Group>

              <Button variant="primary" type="submit" className="w-100 py-2 fw-semibold">
                Iniciar sesión
              </Button>
            </Form>

            <div className="text-center mt-4">
              <span className="text-muted">¿No tienes cuenta? </span>
              <Link to="/registro" className="text-decoration-none fw-semibold">
                Regístrate
              </Link>
            </div>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  )
}

export default Login