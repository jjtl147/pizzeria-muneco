import { useState, useEffect } from 'react'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import Spinner from 'react-bootstrap/Spinner'
import Alert from 'react-bootstrap/Alert'
import Button from 'react-bootstrap/Button'
import axios from 'axios'
import ProductCard from '../components/ProductCard'

// URL base del backend de Flask
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

function Catalogo() {
  // Estados para gestionar los productos, la carga y posibles errores
  const [productos, setProductos] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  // Carga inicial al montar el componente
  useEffect(() => {
    let cancelado = false

    const consultarProductos = async () => {
      try {
        setError(null)
        const respuesta = await axios.get(`${API_URL}/api/productos`)
        
        if (!cancelado) {
          if (respuesta.data && respuesta.data.data) {
            setProductos(respuesta.data.data)
          } else {
            setProductos([])
          }
        }
      } catch (err) {
        if (!cancelado) {
          console.error('Error al consultar productos:', err)
          setError('No se pudo conectar con el servidor. Verifica que el backend esté en ejecución.')
        }
      } finally {
        if (!cancelado) {
          setCargando(false)
        }
      }
    }

    consultarProductos()

    return () => {
      cancelado = true
    }
  }, [])

  // Función para reintentar la carga manualmente
  const reintentarCarga = async () => {
    setCargando(true)
    setError(null)
    try {
      const respuesta = await axios.get(`${API_URL}/api/productos`)
      if (respuesta.data && respuesta.data.data) {
        setProductos(respuesta.data.data)
      } else {
        setProductos([])
      }
    } catch (err) {
      console.error('Error al reintentar carga de productos:', err)
      setError('No se pudo conectar con el servidor. Verifica que el backend esté en ejecución.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="py-4">
      <h2 className="mb-4 text-center">Nuestro menú</h2>

      {/* 1. Estado de Carga (Spinner) */}
      {cargando && (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" role="status">
            <span className="visually-hidden">Cargando productos...</span>
          </Spinner>
          <p className="mt-3 text-muted">Cargando nuestro menú artesanal...</p>
        </div>
      )}

      {/* 2. Estado de Error */}
      {error && !cargando && (
        <Alert variant="danger" className="text-center my-4">
          <Alert.Heading>Error al cargar el menú</Alert.Heading>
          <p className="mb-3">{error}</p>
          <Button variant="outline-danger" size="sm" onClick={reintentarCarga}>
            Reintentar
          </Button>
        </Alert>
      )}

      {/* 3. Catálogo vacío */}
      {!cargando && !error && productos.length === 0 && (
        <Alert variant="info" className="text-center my-4">
          No hay productos disponibles en este momento. Vuelve a consultar más tarde.
        </Alert>
      )}

      {/* 4. Grid de Productos (cuando existen datos) */}
      {!cargando && !error && productos.length > 0 && (
        <Row xs={1} sm={2} md={3} lg={4} className="g-4">
          {productos.map((producto) => (
            <Col key={producto.id}>
              <ProductCard
                id={producto.id}
                nombre={producto.nombre}
                descripcion={producto.descripcion}
                precio={producto.precio}
                imagen={producto.imagen}
              />
            </Col>
          ))}
        </Row>
      )}
    </div>
  )
}

export default Catalogo