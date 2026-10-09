import { useState } from 'react'
import { Alert, Button, Form, Table } from 'react-bootstrap'
import api, { mensajeError } from '../../services/api'
import useConsulta from '../../hooks/useConsulta'
import EstadoConsulta from '../../components/EstadoConsulta'
import Paginacion from '../../components/Paginacion'
export default function Categorias() {
  const [pagina, setPagina] = useState(1)
  const consulta = useConsulta(`/api/admin/categorias?pagina=${pagina}`)
  const [form, setForm] = useState({ nombre: '', descripcion: '', activo: true })
  const [id, setId] = useState(null)
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  async function guardar(e) {
    e.preventDefault(); setError(''); setOcupado(true)
    try {
      if (id) await api.put(`/api/categorias/${id}`, form)
      else await api.post('/api/categorias', form)
      setId(null); setForm({ nombre: '', descripcion: '', activo: true }); consulta.recargar()
    } catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  return <><h2 className="h4">Categorías</h2>{error && <Alert variant="danger">{error}</Alert>}
    <Form onSubmit={guardar} className="mb-4"><fieldset disabled={ocupado}>
      <h3 className="h5">{id ? 'Editar categoría' : 'Nueva categoría'}</h3>
      <Form.Group className="mb-2" controlId="categoria-nombre"><Form.Label>Nombre</Form.Label><Form.Control required maxLength={50} value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} /></Form.Group>
      <Form.Group className="mb-2" controlId="categoria-descripcion"><Form.Label>Descripción</Form.Label><Form.Control value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} /></Form.Group>
      <Form.Check id="categoria-activa" label="Activa" checked={form.activo} onChange={(e) => setForm({ ...form, activo: e.target.checked })} />
      <Button type="submit" className="mt-2">Guardar</Button>
      <Button className="ms-2 mt-2" variant="outline-secondary" onClick={() => { setId(null); setForm({ nombre: '', descripcion: '', activo: true }) }}>Cancelar edición</Button>
    </fieldset></Form><EstadoConsulta {...consulta} />
    <Table responsive striped><thead><tr><th>Nombre</th><th>Descripción</th><th>Activa</th><th>Acciones</th></tr></thead><tbody>
      {consulta.data.map((c) => <tr key={c.id}><td>{c.nombre}</td><td>{c.descripcion}</td><td>{c.activo ? 'Sí' : 'No'}</td><td><Button size="sm" onClick={() => { setId(c.id); setForm({ nombre: c.nombre, descripcion: c.descripcion || '', activo: c.activo }) }}>Editar</Button></td></tr>)}
    </tbody></Table><Paginacion pagina={pagina} cambiar={setPagina} {...consulta} />
  </>
}
