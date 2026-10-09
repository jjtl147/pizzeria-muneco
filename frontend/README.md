# Frontend de Pizzería Muñeco

React 19 + Vite + JavaScript, Bootstrap y React Bootstrap, React Router, Axios y
Context API. Node y pnpm son necesarios.

1. Ejecutar `pnpm install` dentro de `frontend/`.
2. Copiar `.env.example` a `.env` y ajustar `VITE_API_URL` si Flask no está en
   `http://localhost:5000`. Reiniciar Vite después de cambiar esa variable.
3. Ejecutar `pnpm dev` y abrir la dirección que imprime Vite.

`pnpm lint` revisa el código; `pnpm build` genera `dist/`.

Rutas públicas: inicio, catálogo, carrito, login y registro.
CLIENTE tiene `/mis-pedidos` y confirmación de compra desde el carrito.
VENDEDOR y ADMINISTRADOR acceden a `/operacion` y `/operacion/ventas`.
Las demás secciones del panel requieren ADMINISTRADOR.

La sesión y el carrito se conservan en `sessionStorage` durante la pestaña.
Cerrar sesión elimina el token y vacía el carrito. Un 401 autenticado cierra la
sesión; un 403 actualiza los permisos. Flask decide el acceso a cada operación,
aunque alguien cambie el JavaScript o los datos almacenados del navegador.

El tamaño elegido identifica una opción de producto con precio/stock propios.
El total del carrito es estimado: PostgreSQL recalcula el pedido con precios reales.
Los pagos son registros operativos; la aplicación no cobra mediante pasarelas.

Las pruebas de navegador están en `tests/`; instrucciones en `backend/README.md`.
