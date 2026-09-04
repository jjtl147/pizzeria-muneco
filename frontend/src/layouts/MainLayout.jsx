import { Outlet, Link } from 'react-router-dom'
import Container from 'react-bootstrap/Container'
import Nav from 'react-bootstrap/Nav'
import Navbar from 'react-bootstrap/Navbar'
import { useContext } from 'react'
import { CartContext } from '../context/CartContext'
function MainLayout() {
  const { totalItems } = useContext(CartContext)
  return (
    <>
      <Navbar bg="dark" variant="dark" expand="lg">
        <Container>
          <Navbar.Brand as={Link} to="/">Pizzería Muñeco</Navbar.Brand>
          <Navbar.Toggle aria-controls="main-navigation" />
          <Navbar.Collapse id="main-navigation">
            <Nav className="ms-auto">
              <Nav.Link as={Link} to="/">Inicio</Nav.Link>
              <Nav.Link as={Link} to="/catalogo">Catálogo</Nav.Link>
              <Nav.Link as={Link} to="/carrito">Carrito ({totalItems})</Nav.Link>
              <Nav.Link as={Link} to="/login">Iniciar sesión</Nav.Link>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <Container className="mt-4">
        <Outlet />
      </Container>
    </>
  )
}

export default MainLayout