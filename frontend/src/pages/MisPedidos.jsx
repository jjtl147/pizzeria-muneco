import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Alert, Badge, Button, Card, Table } from 'react-bootstrap'
import useConsulta from '../hooks/useConsulta'
import EstadoConsulta from '../components/EstadoConsulta'
import Paginacion from '../components/Paginacion'
import { dinero, fecha, nombreProducto } from '../utils/formato'
export default function MisPedidos() {
  const [pagina, setPagina] = useState(1)
  const consulta = useConsulta(`/api/pedidos/mis-pedidos?pagina=${pagina}`)
  const location = useLocation()
  return <div className="py-4"><h1 className="h3">Mis pedidos</h1>
    {location.state?.mensaje && <Alert variant="success">{location.state.mensaje}</Alert>}
    <Button className="mb-3" variant="outline-primary" onClick={consulta.recargar} disabled={consulta.cargando}>Actualizar</Button>
    <EstadoConsulta {...consulta} />
    {!consulta.cargando && !consulta.error && consulta.data.length === 0 && <Alert variant="info">Todavía no tienes pedidos.</Alert>}
    {consulta.data.map((p) => <Card key={p.id} className="mb-3"><Card.Body>
      <h2 className="h5">Pedido #{p.id} <Badge>{p.estado.replaceAll('_', ' ')}</Badge></h2>
      <p>{fecha(p.fecha_pedido)} · {p.direccion_entrega} · {p.metodo_pago}</p>
      <Table responsive><thead><tr><th>Producto</th><th>Cantidad</th><th>Subtotal</th></tr></thead><tbody>
        {p.detalle_pedidos.map((d) => <tr key={d.id}><td>{nombreProducto(d.nombre_producto ? d : d.productos || {})}</td><td>{d.cantidad}</td><td>{dinero(d.subtotal)}</td></tr>)}
      </tbody></Table><strong>Total: {dinero(p.total)}</strong>
    </Card.Body></Card>)}
    <Paginacion pagina={pagina} cambiar={setPagina} {...consulta} />
  </div>
}
