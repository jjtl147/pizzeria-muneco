import { useContext, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert, Button, Form, Card } from 'react-bootstrap'
import { CartContext } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import CarritoVista from '../components/CarritoVista'
import api, { mensajeError } from '../services/api'

export default function Carrito() {
  const carrito = useContext(CartContext)
  const { usuario, tieneRol } = useAuth()
  const navigate = useNavigate()
  const [direccion, setDireccion] = useState(usuario?.direccion || '')
  const [telefono, setTelefono] = useState(usuario?.telefono || '')
  const [pago, setPago] = useState('EFECTIVO')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  async function confirmar(e) {
    e.preventDefault(); setError(''); setEnviando(true)
    try {
      const { data } = await api.post('/api/pedidos', {
        direccion_entrega: direccion, telefono_contacto: telefono, metodo_pago: pago,
        items: carrito.items.map((item) => ({ producto_id: item.id, cantidad: item.cantidad })),
      })
      carrito.vaciarCarrito()
      navigate('/mis-pedidos', { state: { mensaje: `Pedido #${data.data.pedido.id} registrado correctamente.` } })
    } catch (err) { setError(mensajeError(err)) } finally { setEnviando(false) }
  }
  return <>
    <fieldset disabled={enviando}><CarritoVista {...carrito} /></fieldset>
    {carrito.items.length > 0 && (!usuario ? <Alert variant="info"><Link to="/login" state={{ desde: '/carrito' }}>Inicia sesión</Link> para confirmar tu pedido.</Alert>
      : !tieneRol('CLIENTE') ? <Alert variant="warning">Necesitas el rol CLIENTE para realizar un pedido personal.</Alert>
      : <Card className="my-4"><Card.Body><h2 className="h4">Confirmar pedido</h2>
        {error && <Alert variant="danger">{error}</Alert>}
        <Form onSubmit={confirmar}><fieldset disabled={enviando}>
          <Form.Group className="mb-3" controlId="entrega-direccion"><Form.Label>Dirección de entrega</Form.Label>
            <Form.Control required value={direccion} onChange={(e) => setDireccion(e.target.value)} /></Form.Group>
          <Form.Group className="mb-3" controlId="entrega-telefono"><Form.Label>Teléfono de contacto</Form.Label>
            <Form.Control type="tel" maxLength={20} value={telefono} onChange={(e) => setTelefono(e.target.value)} /></Form.Group>
          <Form.Group className="mb-3" controlId="entrega-pago"><Form.Label>Método de pago</Form.Label>
            <Form.Select value={pago} onChange={(e) => setPago(e.target.value)}>{['EFECTIVO', 'QR', 'TARJETA'].map((m) => <option key={m}>{m}</option>)}</Form.Select>
            <Form.Text>El pago lo confirma el personal al entregar el pedido.</Form.Text></Form.Group>
          <Button type="submit">{enviando ? 'Registrando...' : 'Confirmar pedido'}</Button>
        </fieldset></Form>
      </Card.Body></Card>)}
  </>
}
