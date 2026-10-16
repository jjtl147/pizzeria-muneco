import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Form } from 'react-bootstrap'
import { useAuth } from '../context/AuthContext'
import api, { mensajeError } from '../services/api'

// Supabase Auth usa el flujo implícito al solicitar enlaces desde Flask.
// Los tokens solo se reciben en el fragmento, nunca en query ni en logs HTTP.
export default function ConfirmarAcceso({ recuperacion = false }) {
  const { aceptarSesion, cerrarSesion } = useAuth()
  const navigate = useNavigate()
  const [enlace] = useState(() => {
    const params = new URLSearchParams(window.location.hash.slice(1))
    return { token: params.get('access_token'), refresh_token: params.get('refresh_token'),
      expires_at: Math.floor(Date.now() / 1000) + Number(params.get('expires_in') || 3600),
      tipo: params.get('type'), error: params.has('error') || params.has('error_code') }
  })
  const [listo, setListo] = useState(false)
  const [error, setError] = useState('')
  const [password, setPassword] = useState('')
  const [confirmacion, setConfirmacion] = useState('')
  const [ocupado, setOcupado] = useState(false)
  useEffect(() => {
    window.history.replaceState(null, '', window.location.pathname)
    let vigente = true
    if (enlace.error || !enlace.token || !enlace.refresh_token || (recuperacion && enlace.tipo !== 'recovery')) {
      // No usar una sesión antigua para sustituir un enlace inválido.
      return () => { vigente = false }
    }
    aceptarSesion(enlace).then(() => { if (vigente) setListo(true) })
      .catch(() => { if (vigente) setError('El enlace venció o no es válido. Solicita uno nuevo.') })
    return () => { vigente = false }
    // Procesar únicamente el enlace recibido al entrar a esta página.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enlace, recuperacion])
  async function guardar(e) {
    e.preventDefault(); setError('')
    if (password !== confirmacion) { setError('Las contraseñas no coinciden.'); return }
    setOcupado(true)
    try {
      await api.put('/api/auth/password', { password }, { headers: { Authorization: `Bearer ${enlace.token}` } })
      cerrarSesion()
      navigate('/login', { replace: true, state: { mensaje: 'Contraseña actualizada. Inicia sesión con la nueva contraseña.' } })
    } catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  const invalido = enlace.error || !enlace.token || !enlace.refresh_token || (recuperacion && enlace.tipo !== 'recovery')
  return <Card className="mx-auto my-4" style={{ maxWidth: 500 }}><Card.Body>
    <h1 className="h3">{recuperacion ? 'Nueva contraseña' : 'Confirmar correo'}</h1>
    {(error || invalido) && <Alert variant="danger">{error || 'El enlace no es válido. Solicita uno nuevo.'}</Alert>}
    {!error && !invalido && !listo && <p>Comprobando enlace...</p>}
    {listo && !recuperacion && <><Alert variant="success">Correo confirmado. Ya puedes usar tu cuenta.</Alert><Link to="/catalogo">Ir al catálogo</Link></>}
    {listo && recuperacion && <Form onSubmit={guardar}>
      <Form.Group controlId="nueva-password" className="mb-3"><Form.Label>Nueva contraseña</Form.Label>
        <Form.Control type="password" required minLength={8} maxLength={256} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} /></Form.Group>
      <Form.Group controlId="confirmar-password" className="mb-3"><Form.Label>Repetir contraseña</Form.Label>
        <Form.Control type="password" required minLength={8} maxLength={256} autoComplete="new-password" value={confirmacion} onChange={(e) => setConfirmacion(e.target.value)} /></Form.Group>
      <Button type="submit" disabled={ocupado}>{ocupado ? 'Guardando...' : 'Guardar contraseña'}</Button>
    </Form>}
    {(error || invalido) && <Link to="/recuperar">Solicitar otro enlace</Link>}
  </Card.Body></Card>
}
