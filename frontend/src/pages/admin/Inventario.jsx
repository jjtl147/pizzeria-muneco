import { useState } from 'react'
import { Alert, Badge, Button, Form, Table } from 'react-bootstrap'
import api, { mensajeError } from '../../services/api'
import useConsulta from '../../hooks/useConsulta'
import EstadoConsulta from '../../components/EstadoConsulta'
import Paginacion from '../../components/Paginacion'
import { nombreProducto } from '../../utils/formato'
function stockProducto(p) { return Array.isArray(p.inventario) ? p.inventario[0] : p.inventario }
export default function Inventario() {
  const [pagina, setPagina] = useState(1)
  const consulta = useConsulta(`/api/inventario?pagina=${pagina}`)
  const [seleccion, setSeleccion] = useState(null)
  const [stock, setStock] = useState(0)
  const [minimo, setMinimo] = useState(5)
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  function editar(p) { setSeleccion(p); setStock(stockProducto(p)?.stock_actual || 0); setMinimo(stockProducto(p)?.stock_minimo ?? 5); setError('') }
  async function guardar(e) {
    e.preventDefault(); setOcupado(true); setError('')
    try {
      await api.put(`/api/inventario/${seleccion.id}`, { stock_actual: Number(stock), stock_minimo: Number(minimo), stock_esperado: stockProducto(seleccion)?.stock_actual ?? null })
      setSeleccion(null); consulta.recargar()
    } catch (err) { setError(mensajeError(err)); consulta.recargar() } finally { setOcupado(false) }
  }
  return <><h2 className="h4">Inventario por producto y tamaño</h2>{error && <Alert variant="danger">{error}</Alert>}
    {seleccion && <Form onSubmit={guardar} className="border p-3 mb-3"><fieldset disabled={ocupado}>
      <h3 className="h5">{nombreProducto(seleccion)}</h3>
      <Form.Group controlId="stock-actual" className="mb-2"><Form.Label>Stock actual</Form.Label><Form.Control type="number" min="0" step="1" required value={stock} onChange={(e) => setStock(e.target.value)} /></Form.Group>
      <Form.Group controlId="stock-minimo" className="mb-2"><Form.Label>Mínimo para alerta</Form.Label><Form.Control type="number" min="0" step="1" required value={minimo} onChange={(e) => setMinimo(e.target.value)} /></Form.Group>
      <Button type="submit">Guardar stock</Button><Button className="ms-2" variant="outline-secondary" onClick={() => setSeleccion(null)}>Cancelar</Button>
    </fieldset></Form>}
    <EstadoConsulta {...consulta} /><Table responsive striped><thead><tr><th>Producto</th><th>Disponible</th><th>Mínimo</th><th>Alerta</th><th>Acciones</th></tr></thead><tbody>
      {consulta.data.map((p) => { const inv = stockProducto(p); return <tr key={p.id}><td>{nombreProducto(p)}</td><td>{inv?.stock_actual ?? 'Sin inventario'}</td><td>{inv?.stock_minimo ?? '—'}</td>
        <td>{!inv ? <Badge bg="secondary">Inicializar</Badge> : inv.stock_actual <= inv.stock_minimo ? <Badge bg="danger">Stock bajo</Badge> : <Badge bg="success">Disponible</Badge>}</td>
        <td><Button size="sm" onClick={() => editar(p)} disabled={ocupado}>Ajustar</Button></td></tr> })}
    </tbody></Table><Paginacion pagina={pagina} cambiar={setPagina} {...consulta} />
  </>
}
