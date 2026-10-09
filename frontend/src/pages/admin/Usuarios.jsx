import { useState } from 'react'
import { Alert, Button, Form, Table, Badge } from 'react-bootstrap'
import api, { mensajeError } from '../../services/api'
import useConsulta from '../../hooks/useConsulta'
import EstadoConsulta from '../../components/EstadoConsulta'
import Paginacion from '../../components/Paginacion'
export default function Usuarios() {
  const [pagina, setPagina] = useState(1)
  const consulta = useConsulta(`/api/usuarios?pagina=${pagina}`)
  const [usuario, setUsuario] = useState(null)
  const [roles, setRoles] = useState([])
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  async function guardar(e) {
    e.preventDefault(); setError(''); setOcupado(true)
    try {
      await api.put(`/api/usuarios/${usuario.id}/roles`, { roles })
      setUsuario(null); consulta.recargar(); window.dispatchEvent(new Event('focus'))
    } catch (err) { setError(mensajeError(err)) } finally { setOcupado(false) }
  }
  return <><h2 className="h4">Usuarios y roles</h2><p>Una persona puede tener varios roles. Siempre debe conservarse al menos un administrador.</p>
    {error && <Alert variant="danger">{error}</Alert>}
    {usuario && <Form onSubmit={guardar} className="border p-3 mb-3"><fieldset disabled={ocupado}><h3 className="h5">Roles de {usuario.nombre}</h3>
      {['CLIENTE', 'VENDEDOR', 'ADMINISTRADOR'].map((rol) => <Form.Check key={rol} id={`usuario-rol-${rol}`} label={rol} checked={roles.includes(rol)}
        onChange={(e) => setRoles(e.target.checked ? [...roles, rol] : roles.filter((r) => r !== rol))} />)}
      <Button className="mt-2" type="submit" disabled={!roles.length}>Guardar roles</Button><Button className="ms-2 mt-2" variant="outline-secondary" onClick={() => setUsuario(null)}>Cancelar</Button>
    </fieldset></Form>}
    <EstadoConsulta {...consulta} /><Table responsive striped><thead><tr><th>Nombre</th><th>Correo</th><th>Roles</th><th>Acciones</th></tr></thead><tbody>
      {consulta.data.map((u) => <tr key={u.id}><td>{u.nombre}</td><td>{u.email}</td><td>{u.roles.map((r) => <Badge key={r} className="me-1">{r}</Badge>)}</td>
        <td><Button size="sm" disabled={ocupado} onClick={() => { setUsuario(u); setRoles(u.roles); setError('') }}>Editar roles</Button></td></tr>)}
    </tbody></Table><Paginacion pagina={pagina} cambiar={setPagina} {...consulta} />
  </>
}
