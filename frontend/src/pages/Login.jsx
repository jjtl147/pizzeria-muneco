import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Card, Form, Button, Row, Col, Alert } from 'react-bootstrap'
import { useAuth } from '../context/AuthContext'
import { mensajeError } from '../services/api'

export default function Login() {
  const { usuario, iniciarSesion } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)
  if (usuario) return <Navigate to={usuario.roles.some((r) => ['ADMINISTRADOR', 'VENDEDOR'].includes(r)) ? '/operacion' : '/catalogo'} replace />
  async function enviar(evento) {
    evento.preventDefault()
    setError(''); setEnviando(true)
    try {
      const cuenta = await iniciarSesion(email, password)
      const destino = location.state?.desde
      navigate(typeof destino === 'string' && destino.startsWith('/') && !destino.startsWith('//')
        ? destino : cuenta.roles.some((r) => ['ADMINISTRADOR', 'VENDEDOR'].includes(r)) ? '/operacion' : '/catalogo', { replace: true })
    } catch (err) { setError(mensajeError(err)) } finally { setEnviando(false) }
  }
  return <Row className="justify-content-center py-5"><Col md={6} lg={5}><Card><Card.Body>
    <h1 className="h3">Iniciar sesión</h1>
    {location.state?.mensaje && <Alert variant="info">{location.state.mensaje}</Alert>}
    {error && <Alert variant="danger">{error}</Alert>}
    <Form onSubmit={enviar}>
      <Form.Group className="mb-3" controlId="loginEmail"><Form.Label>Correo electrónico</Form.Label>
        <Form.Control type="email" required autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} /></Form.Group>
      <Form.Group className="mb-3" controlId="loginPassword"><Form.Label>Contraseña</Form.Label>
        <Form.Control type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} /></Form.Group>
      <Button type="submit" disabled={enviando}>{enviando ? 'Ingresando...' : 'Iniciar sesión'}</Button>
    </Form>
    <p className="mt-3">¿No tienes cuenta? <Link to="/registro">Regístrate</Link></p>
  </Card.Body></Card></Col></Row>
}
