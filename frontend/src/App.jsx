import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import OperacionLayout from './layouts/OperacionLayout'
import Home from './pages/Home'
import Catalogo from './pages/Catalogo'
import Carrito from './pages/Carrito'
import Login from './pages/Login'
import Registro from './pages/Registro'
import Recuperar from './pages/Recuperar'
import ConfirmarAcceso from './pages/ConfirmarAcceso'
import MisPedidos from './pages/MisPedidos'
import Pedidos from './pages/admin/Pedidos'
import Ventas from './pages/admin/Ventas'
import Productos from './pages/admin/Productos'
import Categorias from './pages/admin/Categorias'
import Inventario from './pages/admin/Inventario'
import Usuarios from './pages/admin/Usuarios'
import Reportes from './pages/admin/Reportes'
import Asistente from './pages/admin/Asistente'
import RutaProtegida from './components/RutaProtegida'
import AuthProvider from './context/AuthProvider'
import { CartProvider } from './context/CartContext'

export default function App() {
  return <AuthProvider><CartProvider><BrowserRouter><Routes>
    <Route element={<MainLayout />}>
      <Route path="/" element={<Home />} /><Route path="/catalogo" element={<Catalogo />} />
      <Route path="/carrito" element={<Carrito />} /><Route path="/login" element={<Login />} /><Route path="/registro" element={<Registro />} />
      <Route path="/recuperar" element={<Recuperar />} />
      <Route path="/restablecer" element={<ConfirmarAcceso key="recuperacion" recuperacion />} />
      <Route path="/auth/callback" element={<ConfirmarAcceso key="confirmacion" />} />
      <Route element={<RutaProtegida roles={['CLIENTE']} />}><Route path="/mis-pedidos" element={<MisPedidos />} /></Route>
      <Route element={<RutaProtegida roles={['ADMINISTRADOR', 'VENDEDOR']} />}>
        <Route path="/operacion" element={<OperacionLayout />}>
          <Route index element={<Pedidos />} /><Route path="ventas" element={<Ventas />} />
          <Route element={<RutaProtegida roles={['ADMINISTRADOR']} />}>
            <Route path="productos" element={<Productos />} /><Route path="categorias" element={<Categorias />} />
            <Route path="inventario" element={<Inventario />} /><Route path="usuarios" element={<Usuarios />} />
            <Route path="reportes" element={<Reportes />} /><Route path="asistente" element={<Asistente />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<div><h1 className="h3">Página no encontrada</h1><Link to="/">Volver al inicio</Link></div>} />
    </Route>
  </Routes></BrowserRouter></CartProvider></AuthProvider>
}
