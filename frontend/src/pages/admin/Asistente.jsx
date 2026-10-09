import { useState } from 'react'
import { Alert, Badge, Button, Card, Form } from 'react-bootstrap'
import api, { mensajeError } from '../../services/api'
import useConsulta from '../../hooks/useConsulta'
import EstadoConsulta from '../../components/EstadoConsulta'

export default function Asistente() {
  const configuracion = useConsulta('/api/integraciones')
  const [mensajes, setMensajes] = useState([])
  const [pregunta, setPregunta] = useState('')
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  async function enviar(e) {
    e.preventDefault(); setError(''); setOcupado(true)
    const historial = [...mensajes.slice(-8), { role: 'user', content: pregunta }]
    try {
      const { data } = await api.post('/api/asistente', { mensajes: historial }, { timeout: 120000 })
      setMensajes([...historial, { role: 'assistant', content: data.respuesta }]); setPregunta('')
    } catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  return <><h2 className="h4">Asistente e integraciones</h2><EstadoConsulta {...configuracion} />
    {!configuracion.cargando && !configuracion.error && <>
      <p>Telegram: <Badge bg={configuracion.data.telegram ? 'success' : 'secondary'}>{configuracion.data.telegram ? 'Habilitado' : 'Sin configurar'}</Badge></p>
      <p>Asistente: <Badge bg={configuracion.data.asistente ? 'success' : 'secondary'}>{configuracion.data.asistente ? 'Habilitado' : 'Sin configurar'}</Badge></p>
      {!configuracion.data.asistente && <Alert variant="info">El asistente todavía no está disponible. El administrador debe configurar el servicio.</Alert>}
    </>}
    <p>Consulta el catálogo, stock y ventas de los últimos siete días.</p>
    {error && <Alert variant="danger">{error}</Alert>}
    <div aria-live="polite">{mensajes.map((m, i) => <Card key={i} className="mb-2" body><strong>{m.role === 'user' ? 'Tú' : 'Asistente'}</strong><p className="mb-0" style={{ whiteSpace: 'pre-wrap' }}>{m.content}</p></Card>)}</div>
    <Form onSubmit={enviar}><Form.Group className="mb-3" controlId="asistente-pregunta"><Form.Label>Tu consulta</Form.Label>
      <Form.Control as="textarea" rows={3} required maxLength={2000} value={pregunta} onChange={(e) => setPregunta(e.target.value)} disabled={ocupado || !configuracion.data.asistente} />
    </Form.Group><Button type="submit" disabled={ocupado || !configuracion.data.asistente}>{ocupado ? 'Consultando...' : 'Enviar consulta'}</Button>
      <Button variant="outline-secondary" className="ms-2" disabled={ocupado} onClick={() => setMensajes([])}>Nueva conversación</Button>
    </Form>
  </>
}
