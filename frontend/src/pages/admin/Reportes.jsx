import { useState } from 'react'
import { Alert, Button, Card, Col, Form, Row, Table } from 'react-bootstrap'
import useConsulta from '../../hooks/useConsulta'
import EstadoConsulta from '../../components/EstadoConsulta'
import { dinero } from '../../utils/formato'

export default function Reportes() {
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [rango, setRango] = useState('')
  const consulta = useConsulta(`/api/reportes/ventas${rango}`)
  const reporte = !Array.isArray(consulta.data) ? consulta.data : null
  function consultar(e) { e.preventDefault(); setRango(`?desde=${desde}&hasta=${hasta}`); consulta.recargar() }
  function exportar() {
    const filas = [['Producto', 'Tamaño', 'Cantidad', 'Total'], ...reporte.por_producto.map((p) => [p.nombre, p.tamano || '', p.cantidad, p.total])]
    // Evitar que un nombre de producto sea interpretado como fórmula en Excel.
    const celda = (valor) => `"${String(valor ?? '').replace(/^[=+@-]/, "'").replaceAll('"', '""')}"`
    const csv = '\uFEFF' + filas.map((f) => f.map(celda).join(',')).join('\r\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    const link = document.createElement('a'); link.href = url; link.download = 'ventas-productos.csv'; link.click(); URL.revokeObjectURL(url)
  }
  return <><h2 className="h4">Ventas y estadísticas</h2><p>Por defecto se muestran los últimos siete días, en horario de Bolivia.</p>
    <Form onSubmit={consultar} className="d-flex gap-3 flex-wrap mb-3">
      <Form.Group controlId="reporte-desde"><Form.Label>Desde</Form.Label><Form.Control type="date" value={desde} onChange={(e) => setDesde(e.target.value)} /></Form.Group>
      <Form.Group controlId="reporte-hasta"><Form.Label>Hasta</Form.Label><Form.Control type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} /></Form.Group>
      <Button type="submit" className="align-self-end" disabled={consulta.cargando}>Consultar</Button>
    </Form><EstadoConsulta {...consulta} />
    {reporte && !consulta.error && <>
      <Row className="g-3 mb-4"><Col md={4}><Card body><h3 className="h6">Ventas cobradas</h3><strong className="fs-3">{dinero(reporte.total)}</strong></Card></Col>
        <Col md={4}><Card body><h3 className="h6">Cantidad de ventas</h3><strong className="fs-3">{reporte.cantidad}</strong></Card></Col>
        <Col md={4}><Card body><h3 className="h6">Promedio por venta</h3><strong className="fs-3">{dinero(reporte.cantidad ? reporte.total / reporte.cantidad : 0)}</strong></Card></Col></Row>
      <h3 className="h5">Ventas por día</h3><Table responsive striped><thead><tr><th>Fecha</th><th>Ventas</th><th>Total</th></tr></thead><tbody>
        {reporte.por_dia.map((d) => <tr key={d.fecha}><td>{d.fecha}</td><td>{d.cantidad}</td><td>{dinero(d.total)}</td></tr>)}
      </tbody></Table><h3 className="h5">Métodos de pago</h3><Table responsive striped><thead><tr><th>Pago</th><th>Ventas</th><th>Total</th></tr></thead><tbody>
        {reporte.por_pago.map((p) => <tr key={p.metodo_pago}><td>{p.metodo_pago}</td><td>{p.cantidad}</td><td>{dinero(p.total)}</td></tr>)}
      </tbody></Table><div className="d-flex gap-3 align-items-center"><h3 className="h5">Ventas por producto y tamaño</h3><Button size="sm" variant="outline-primary" onClick={exportar}>Descargar CSV</Button></div>
      <Table responsive striped><thead><tr><th>Producto</th><th>Tamaño</th><th>Unidades</th><th>Total</th></tr></thead><tbody>
        {reporte.por_producto.map((p, i) => <tr key={i}><td>{p.nombre}</td><td>{p.tamano || 'Único'}</td><td>{p.cantidad}</td><td>{dinero(p.total)}</td></tr>)}
      </tbody></Table><h3 className="h5">Consumo de productos en el periodo</h3>
      <Alert variant="info">Unidades reservadas o vendidas por pedidos no cancelados. No representa consumo de ingredientes.</Alert>
      <Table responsive striped><thead><tr><th>Producto</th><th>Tamaño</th><th>Unidades</th></tr></thead><tbody>
        {reporte.consumo.map((p, i) => <tr key={i}><td>{p.nombre}</td><td>{p.tamano || 'Único'}</td><td>{p.cantidad}</td></tr>)}
      </tbody></Table>
    </>}
  </>
}
