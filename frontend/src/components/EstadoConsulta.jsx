import { Alert, Button, Spinner } from 'react-bootstrap'
export default function EstadoConsulta({ cargando, error, recargar }) {
  if (cargando) return <Spinner animation="border" role="status"><span className="visually-hidden">Cargando...</span></Spinner>
  if (error) return <Alert variant="danger">{error} <Button variant="outline-danger" onClick={recargar}>Reintentar</Button></Alert>
  return null
}
