import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Form, Button, Alert, Card } from 'react-bootstrap'
import api, { mensajeError } from '../services/api'

export default function Registro() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ nombre: '', email: '', password: '', telefono: '', direccion: '' })
  const [confirmacion, setConfirmacion] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)
  async function enviar(e) {
    e.preventDefault(); setError('')
    if (form.password !== confirmacion) { setError('Las contraseñas no coinciden.'); return }
    setEnviando(true)
    try {
      const { data } = await api.post('/api/auth/registro', form)
      navigate('/login', { replace: true, state: { mensaje: data.mensaje } })
    } catch (err) { setError(mensajeError(err)) } finally { setEnviando(false) }
  }
  return <Card className="mx-auto my-4" style={{ maxWidth: 560 }}><Card.Body>
    <h1 className="h3">Crear cuenta</h1>{error && <Alert variant="danger">{error}</Alert>}
    <Form onSubmit={enviar}>
      {Object.entries({ nombre: 'Nombre', email: 'Correo electrónico', password: 'Contraseña', telefono: 'Teléfono', direccion: 'Dirección' }).map(([campo, etiqueta]) =>
        <Form.Group key={campo} className="mb-3" controlId={`registro-${campo}`}><Form.Label>{etiqueta}</Form.Label>
          <Form.Control value={form[campo]} type={campo === 'password' ? 'password' : campo === 'email' ? 'email' : campo === 'telefono' ? 'tel' : 'text'}
            required={['nombre', 'email', 'password'].includes(campo)} minLength={campo === 'password' ? 8 : undefined}
            maxLength={campo === 'nombre' ? 100 : campo === 'email' ? 150 : campo === 'telefono' ? 20 : undefined}
            autoComplete={campo === 'password' ? 'new-password' : undefined}
            onChange={(e) => setForm({ ...form, [campo]: e.target.value })} /></Form.Group>)}
      <Form.Group className="mb-3" controlId="registro-confirmacion"><Form.Label>Repetir contraseña</Form.Label>
        <Form.Control type="password" required autoComplete="new-password" value={confirmacion} onChange={(e) => setConfirmacion(e.target.value)} /></Form.Group>
      <Button type="submit" disabled={enviando}>{enviando ? 'Creando cuenta...' : 'Registrarme'}</Button>
    </Form><Link className="d-block mt-3" to="/login">Ya tengo una cuenta</Link>
  </Card.Body></Card>
}
