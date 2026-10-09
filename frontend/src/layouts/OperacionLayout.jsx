import { NavLink, Outlet } from 'react-router-dom'
import { Nav } from 'react-bootstrap'
import { useAuth } from '../context/AuthContext'
export default function OperacionLayout() {
  const { tieneRol } = useAuth()
  return <div className="py-3"><h1 className="h3">Panel operativo</h1><Nav variant="pills" className="gap-2 mb-4 flex-wrap">
    <Nav.Link as={NavLink} end to="/operacion">Pedidos</Nav.Link>
    <Nav.Link as={NavLink} to="/operacion/ventas">Ventas</Nav.Link>
    {tieneRol('ADMINISTRADOR') && <>
      <Nav.Link as={NavLink} to="/operacion/productos">Productos</Nav.Link>
      <Nav.Link as={NavLink} to="/operacion/categorias">Categorías</Nav.Link>
      <Nav.Link as={NavLink} to="/operacion/inventario">Inventario</Nav.Link>
      <Nav.Link as={NavLink} to="/operacion/usuarios">Usuarios y roles</Nav.Link>
      <Nav.Link as={NavLink} to="/operacion/reportes">Reportes</Nav.Link>
      <Nav.Link as={NavLink} to="/operacion/asistente">Asistente</Nav.Link>
    </>}
  </Nav><Outlet /></div>
}
