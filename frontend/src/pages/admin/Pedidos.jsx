import { useState } from 'react'
import { Alert, Badge, Button, Card, Form, Table } from 'react-bootstrap'
import api, { mensajeError } from '../../services/api'
import useConsulta from '../../hooks/useConsulta'
import EstadoConsulta from '../../components/EstadoConsulta'
import Paginacion from '../../components/Paginacion'
import { dinero, fecha, nombreProducto } from '../../utils/formato'
const siguientes = { PENDIENTE: ['EN_PREPARACION', 'CANCELADO'], EN_PREPARACION: ['EN_CAMINO', 'CANCELADO'], EN_CAMINO: ['ENTREGADO', 'CANCELADO'] }
export default function Pedidos() {
  const [pagina, setPagina] = useState(1)
  const consulta = useConsulta(`/api/pedidos?pagina=${pagina}`)
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [pagos, setPagos] = useState({})
  async function cambiar(p, estado) {
    if (estado === 'CANCELADO' && !window.confirm(`¿Cancelar el pedido #${p.id} y devolver su stock?`)) return
    setError(''); setOcupado(true)
    try { await api.put(`/api/pedidos/${p.id}/estado`, { estado }); consulta.recargar() }
    catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  async function cobrar(p) {
    setError(''); setOcupado(true)
    try { await api.post('/api/ventas', { pedido_id: p.id, metodo_pago: pagos[p.id] || 'EFECTIVO' }); consulta.recargar() }
    catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  return <><h2 className="h4">Gestión de pedidos</h2><Button className="mb-3" variant="outline-primary" disabled={consulta.cargando} onClick={consulta.recargar}>Actualizar pedidos</Button>
    {error && <Alert variant="danger">{error}</Alert>}<EstadoConsulta {...consulta} />
    {!consulta.cargando && !consulta.error && !consulta.data.length && <Alert variant="info">No hay pedidos.</Alert>}
    {consulta.data.map((p) => <Card key={p.id} className="mb-3"><Card.Body>
      <h3 className="h5">Pedido #{p.id} <Badge>{p.estado.replaceAll('_', ' ')}</Badge></h3>
      <p>{p.usuarios?.nombre || 'Usuario eliminado'} · {fecha(p.fecha_pedido)} · {p.direccion_entrega} · {p.telefono_contacto || 'Sin teléfono'}</p>
      <Table responsive size="sm"><thead><tr><th>Producto</th><th>Cantidad</th><th>Subtotal</th></tr></thead><tbody>
        {p.detalle_pedidos.map((d) => <tr key={d.id}><td>{nombreProducto(d)}</td><td>{d.cantidad}</td><td>{dinero(d.subtotal)}</td></tr>)}
      </tbody></Table><p><strong>Total: {dinero(p.total)}</strong></p>
      <div className="d-flex gap-2 flex-wrap">{(siguientes[p.estado] || []).map((estado) => <Button key={estado} size="sm" disabled={ocupado}
        variant={estado === 'CANCELADO' ? 'outline-danger' : 'primary'} onClick={() => cambiar(p, estado)}>{estado === 'CANCELADO' ? 'Cancelar' : `Pasar a ${estado.replaceAll('_', ' ').toLowerCase()}`}</Button>)}</div>
      {p.estado === 'ENTREGADO' && (!p.ventas || (Array.isArray(p.ventas) && !p.ventas.length)) && <div className="d-flex gap-2 mt-3">
        <Form.Select aria-label={`Pago del pedido ${p.id}`} value={pagos[p.id] || 'EFECTIVO'} disabled={ocupado} onChange={(e) => setPagos({ ...pagos, [p.id]: e.target.value })}>
          {['EFECTIVO', 'QR', 'TARJETA'].map((m) => <option key={m}>{m}</option>)}</Form.Select><Button disabled={ocupado} onClick={() => cobrar(p)}>Registrar cobro</Button></div>}
      {p.ventas && (!Array.isArray(p.ventas) || p.ventas.length > 0) && <Badge bg="success" className="mt-2">Venta registrada</Badge>}
    </Card.Body></Card>)}<Paginacion pagina={pagina} cambiar={setPagina} {...consulta} />
  </>
}
