import { useState } from 'react'
import { Alert, Button, Form, Table, Card } from 'react-bootstrap'
import api, { mensajeError } from '../../services/api'
import useConsulta from '../../hooks/useConsulta'
import EstadoConsulta from '../../components/EstadoConsulta'
import Paginacion from '../../components/Paginacion'
import { dinero, nombreProducto } from '../../utils/formato'
const inicial = { nombre: '', descripcion: '', precio: '', tamano: '', imagen: '', categoria_id: '', stock_inicial: 0, activo: true }
export default function Productos() {
  const [pagina, setPagina] = useState(1)
  const consulta = useConsulta(`/api/admin/productos?pagina=${pagina}`)
  const categorias = useConsulta('/api/categorias')
  const [form, setForm] = useState(inicial)
  const [id, setId] = useState(null)
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  function editar(p) { setId(p.id); setForm({ ...inicial, ...p, categoria_id: p.categoria_id || '', tamano: p.tamano || '', descripcion: p.descripcion || '', imagen: p.imagen || '' }); setError('') }
  function limpiar() { setId(null); setForm(inicial); setError('') }
  async function guardar(e) {
    e.preventDefault(); setError(''); setOcupado(true)
    const datos = { ...form, precio: Number(form.precio), categoria_id: form.categoria_id ? Number(form.categoria_id) : null, stock_inicial: Number(form.stock_inicial) }
    delete datos.id; delete datos.creado_en
    try {
      if (id) await api.put(`/api/productos/${id}`, datos)
      else await api.post('/api/productos', datos)
      limpiar(); consulta.recargar()
    } catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  async function desactivar(p) {
    if (!window.confirm(`¿Desactivar ${nombreProducto(p)}?`)) return
    setOcupado(true); setError('')
    try { await api.delete(`/api/productos/${p.id}`); consulta.recargar() } catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  return <><h2 className="h4">Productos y tamaños</h2><p>Crea una opción por tamaño, con su propio precio y stock.</p>
    {error && <Alert variant="danger">{error}</Alert>}
    <Card className="mb-4"><Card.Body><h3 className="h5">{id ? `Editar producto #${id}` : 'Nuevo producto'}</h3>
      <Form onSubmit={guardar}><fieldset disabled={ocupado} className="row g-3">
        {Object.entries({ nombre: 'Nombre de pizza o producto', tamano: 'Tamaño (opcional)', precio: 'Precio', descripcion: 'Descripción', imagen: 'URL de imagen' }).map(([campo, etiqueta]) =>
          <Form.Group className="col-md-6" key={campo} controlId={`producto-${campo}`}><Form.Label>{etiqueta}</Form.Label>
            <Form.Control type={campo === 'precio' ? 'number' : campo === 'imagen' ? 'url' : 'text'} required={['nombre', 'precio'].includes(campo)}
              min={campo === 'precio' ? 0 : undefined} step={campo === 'precio' ? '0.01' : undefined}
              maxLength={campo === 'nombre' ? 100 : campo === 'tamano' ? 40 : undefined}
              value={form[campo]} onChange={(e) => setForm({ ...form, [campo]: e.target.value })} /></Form.Group>)}
        <Form.Group className="col-md-6" controlId="producto-categoria"><Form.Label>Categoría</Form.Label>
          <Form.Select value={form.categoria_id} onChange={(e) => setForm({ ...form, categoria_id: e.target.value })}><option value="">Sin categoría</option>
            {categorias.data.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            {form.categoria_id && !categorias.data.some((c) => c.id === Number(form.categoria_id)) && <option value={form.categoria_id}>Categoría actual (inactiva)</option>}
          </Form.Select></Form.Group>
        {!id && <Form.Group className="col-md-6" controlId="producto-stock"><Form.Label>Stock inicial</Form.Label>
          <Form.Control type="number" min="0" step="1" required value={form.stock_inicial} onChange={(e) => setForm({ ...form, stock_inicial: e.target.value })} /></Form.Group>}
        {id && <Form.Check id="producto-activo" className="ms-3" label="Producto activo" checked={form.activo} onChange={(e) => setForm({ ...form, activo: e.target.checked })} />}
        <div className="d-flex gap-2"><Button type="submit">{ocupado ? 'Guardando...' : 'Guardar'}</Button><Button variant="outline-secondary" onClick={limpiar}>Limpiar formulario</Button></div>
      </fieldset></Form></Card.Body></Card>
    <EstadoConsulta {...consulta} />
    <Table responsive striped><thead><tr><th>Producto</th><th>Precio</th><th>Activo</th><th>Acciones</th></tr></thead><tbody>
      {consulta.data.map((p) => <tr key={p.id}><td>{nombreProducto(p)}</td><td>{dinero(p.precio)}</td><td>{p.activo ? 'Sí' : 'No'}</td>
        <td><Button size="sm" disabled={ocupado} onClick={() => editar(p)}>Editar</Button>{p.activo && <Button className="ms-2" size="sm" variant="outline-danger" disabled={ocupado} onClick={() => desactivar(p)}>Desactivar</Button>}</td></tr>)}
    </tbody></Table><Paginacion pagina={pagina} cambiar={setPagina} {...consulta} />
  </>
}
