import { BrowserRouter, Routes, Route } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Home from './pages/Home'
import Catalogo from './pages/Catalogo'
import Carrito from './pages/Carrito'
import Login from './pages/Login'
import { CartProvider } from './context/CartContext'

function App() {
  return (
    <CartProvider>
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/catalogo" element={<Catalogo />} />
          <Route path="/carrito" element={<Carrito />} />
          <Route path="/login" element={<Login />} />
        </Route>
      </Routes>
    </BrowserRouter>
    </CartProvider>
  )
}
export default App