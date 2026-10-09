import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Alert, Spinner } from 'react-bootstrap'
import { useAuth } from '../context/AuthContext'

export default function RutaProtegida({ roles }) {
  const { usuario, cargando, tieneRol, errorSesion } = useAuth()
  const location = useLocation()
  if (cargando) return <Spinner animation="border" role="status"><span className="visually-hidden">Verificando sesión...</span></Spinner>
  if (!usuario) return <Navigate to="/login" replace state={{ desde: location.pathname, mensaje: errorSesion }} />
  if (!tieneRol(...roles)) return <Alert variant="warning">No tienes permisos para acceder a esta sección.</Alert>
  return <Outlet />
}
