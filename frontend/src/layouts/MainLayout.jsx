import { Outlet, Link } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import Nav from 'react-bootstrap/Nav'
import Navbar from 'react-bootstrap/Navbar'
import './MainLayout.css'

function MainLayout() {
  return (
    <div className="app-shell">
      <Navbar expand="lg" className="site-navbar">
        <Container>
          <Navbar.Brand as={Link} to="/" className="brand-mark">
            Pizzería Muñeco
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="main-navigation" />
          <Navbar.Collapse id="main-navigation">
            <Nav className="ms-auto">
              <Nav.Link as={Link} to="/">Inicio</Nav.Link>
              <Nav.Link as={Link} to="/catalogo">Catálogo</Nav.Link>
              <Nav.Link as={Link} to="/carrito">Carrito</Nav.Link>
              <Nav.Link as={Link} to="/login">Iniciar sesión</Nav.Link>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <main className="home-page">
        <Container>
          <Outlet />
        </Container>
      </main>
    </div>
  )
}

export default MainLayout