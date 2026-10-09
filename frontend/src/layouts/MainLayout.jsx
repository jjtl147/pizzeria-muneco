import { Outlet, Link, useNavigate } from 'react-router-dom'
import { Container, Nav, Navbar, Button, Alert } from 'react-bootstrap'
import { useContext } from 'react'
import { CartContext } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
export default function MainLayout() {
  const { totalItems } = useContext(CartContext)
  const { usuario, tieneRol, cerrarSesion, errorSesion } = useAuth()
  const navigate = useNavigate()
  function salir() { cerrarSesion(); navigate('/') }
  return <>
    <Navbar bg="dark" variant="dark" expand="lg"><Container>
      <Navbar.Brand as={Link} to="/">Pizzería Muñeco</Navbar.Brand>
      <Navbar.Toggle aria-controls="main-navigation" /><Navbar.Collapse id="main-navigation"><Nav className="ms-auto align-items-lg-center">
        <Nav.Link as={Link} to="/">Inicio</Nav.Link><Nav.Link as={Link} to="/catalogo">Catálogo</Nav.Link>
        <Nav.Link as={Link} to="/carrito">Carrito ({totalItems})</Nav.Link>
        {tieneRol('CLIENTE') && <Nav.Link as={Link} to="/mis-pedidos">Mis pedidos</Nav.Link>}
        {tieneRol('ADMINISTRADOR', 'VENDEDOR') && <Nav.Link as={Link} to="/operacion">Panel operativo</Nav.Link>}
        {usuario ? <><Navbar.Text className="mx-2">{usuario.nombre}</Navbar.Text><Button variant="outline-light" size="sm" onClick={salir}>Cerrar sesión</Button></>
          : <Nav.Link as={Link} to="/login">Iniciar sesión</Nav.Link>}
      </Nav></Navbar.Collapse>
    </Container></Navbar>
    <Container className="mt-4">{errorSesion && usuario && <Alert variant="warning">{errorSesion}</Alert>}<Outlet /></Container>
  </>
}
