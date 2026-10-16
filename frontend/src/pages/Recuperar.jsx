import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Card, Form } from 'react-bootstrap'
import api, { mensajeError } from '../services/api'

export default function Recuperar() {
  const [email, setEmail] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  async function enviar(e) {
    e.preventDefault(); setError(''); setMensaje(''); setOcupado(true)
    try {
      const { data } = await api.post('/api/auth/recuperar', { email })
      setMensaje(data.mensaje)
    } catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  return <Card className="mx-auto my-4" style={{ maxWidth: 500 }}><Card.Body>
    <h1 className="h3">Recuperar acceso</h1>
    <p>Te enviaremos un enlace para definir una contraseña nueva.</p>
    {mensaje && <Alert variant="success">{mensaje}</Alert>}{error && <Alert variant="danger">{error}</Alert>}
    <Form onSubmit={enviar}>
      <Form.Group controlId="recuperar-email" className="mb-3"><Form.Label>Correo electrónico</Form.Label>
        <Form.Control type="email" required maxLength={150} autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      </Form.Group>
      <Button type="submit" disabled={ocupado}>{ocupado ? 'Enviando...' : 'Enviar enlace'}</Button>
    </Form><Link className="d-block mt-3" to="/login">Volver a iniciar sesión</Link>
  </Card.Body></Card>
}
