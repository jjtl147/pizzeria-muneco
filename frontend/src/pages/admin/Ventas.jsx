import { useState } from 'react'
import { Alert, Button, Form, Table, Card } from 'react-bootstrap'
import api, { mensajeError } from '../../services/api'
import useConsulta from '../../hooks/useConsulta'
import EstadoConsulta from '../../components/EstadoConsulta'
import Paginacion from '../../components/Paginacion'
import { dinero, fecha, nombreProducto } from '../../utils/formato'
export default function Ventas() {
  const [pagina, setPagina] = useState(1)
  const consulta = useConsulta(`/api/ventas?pagina=${pagina}`)
  const catalogo = useConsulta('/api/productos')
  const [productoId, setProductoId] = useState('')
  const [cantidad, setCantidad] = useState(1)
  const [items, setItems] = useState([])
  const [pago, setPago] = useState('EFECTIVO')
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [ocupado, setOcupado] = useState(false)
  function agregar(e) {
    e.preventDefault()
    const producto = catalogo.data.find((p) => p.id === Number(productoId))
    if (!producto || !Number.isInteger(Number(cantidad)) || Number(cantidad) < 1) return
    setItems((actuales) => actuales.some((p) => p.id === producto.id) ? actuales.map((p) => p.id === producto.id ? { ...p, cantidad: p.cantidad + Number(cantidad) } : p) : [...actuales, { ...producto, cantidad: Number(cantidad) }])
  }
  async function vender() {
    if (!window.confirm('¿Confirmar esta venta y su pago recibido?')) return
    setOcupado(true); setError(''); setMensaje('')
    try {
      const { data } = await api.post('/api/ventas', { metodo_pago: pago, items: items.map((p) => ({ producto_id: p.id, cantidad: p.cantidad })) })
      setItems([]); setMensaje(`Venta registrada para el pedido #${data.data.pedido_id}.`); consulta.recargar(); catalogo.recargar()
    } catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  return <><h2 className="h4">Ventas</h2>{error && <Alert variant="danger">{error}</Alert>}{mensaje && <Alert variant="success">{mensaje}</Alert>}
    <Card className="mb-4"><Card.Body><h3 className="h5">Registrar venta en local</h3><EstadoConsulta {...catalogo} />
      <Form onSubmit={agregar} className="mb-3"><fieldset className="d-flex gap-2 flex-wrap" disabled={ocupado || catalogo.cargando}>
        <Form.Select aria-label="Producto y tamaño" required value={productoId} onChange={(e) => setProductoId(e.target.value)}><option value="">Seleccionar producto</option>
          {catalogo.data.map((p) => <option key={p.id} value={p.id}>{nombreProducto(p)} — {dinero(p.precio)}</option>)}</Form.Select>
        <Form.Control aria-label="Cantidad" type="number" min="1" step="1" required value={cantidad} onChange={(e) => setCantidad(e.target.value)} />
        <Button type="submit">Agregar producto</Button>
      </fieldset></Form>
      <Table responsive><thead><tr><th>Producto</th><th>Cantidad</th><th>Subtotal</th><th>Acciones</th></tr></thead><tbody>
        {items.map((p) => <tr key={p.id}><td>{nombreProducto(p)}</td><td>{p.cantidad}</td><td>{dinero(p.cantidad * p.precio)}</td><td><Button size="sm" variant="outline-danger" disabled={ocupado} onClick={() => setItems(items.filter((i) => i.id !== p.id))}>Quitar</Button></td></tr>)}
      </tbody></Table><p>Total estimado: <strong>{dinero(items.reduce((t, p) => t + p.precio * p.cantidad, 0))}</strong></p>
      <Form.Group controlId="venta-pago" className="mb-3"><Form.Label>Pago recibido</Form.Label><Form.Select value={pago} disabled={ocupado} onChange={(e) => setPago(e.target.value)}>{['EFECTIVO', 'QR', 'TARJETA'].map((m) => <option key={m}>{m}</option>)}</Form.Select></Form.Group>
      <Button disabled={ocupado || !items.length} onClick={vender}>{ocupado ? 'Registrando...' : 'Confirmar venta'}</Button>
    </Card.Body></Card><h3 className="h5">Ventas registradas</h3><EstadoConsulta {...consulta} />
    <Table responsive striped><thead><tr><th>Venta</th><th>Pedido</th><th>Fecha</th><th>Vendedor</th><th>Pago</th><th>Total</th></tr></thead><tbody>
      {consulta.data.map((v) => <tr key={v.id}><td>#{v.id}</td><td>#{v.pedido_id}</td><td>{fecha(v.fecha_venta)}</td><td>{v.usuarios?.nombre || '—'}</td><td>{v.metodo_pago}</td><td>{dinero(v.total)}</td></tr>)}
    </tbody></Table><Paginacion pagina={pagina} cambiar={setPagina} {...consulta} />
  </>
}
