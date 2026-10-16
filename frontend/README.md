# Frontend de Pizzería Muñeco

React 19 + Vite + JavaScript, Bootstrap y React Bootstrap, React Router, Axios y
Context API. Node y pnpm son necesarios.

1. Ejecutar `pnpm install` dentro de `frontend/`.
2. Copiar `.env.example` a `.env` y ajustar `VITE_API_URL` si Flask no está en
   `http://localhost:5000`. Reiniciar Vite después de cambiar esa variable.
3. Ejecutar `pnpm dev` y abrir la dirección que imprime Vite.

`pnpm lint` revisa el código; `pnpm build` genera `dist/`.

Rutas públicas: inicio, catálogo, carrito, login, registro, `/recuperar`,
`/restablecer` y `/auth/callback`. El registro puede requerir confirmar correo.
Antes de usar Auth, completar [SUPABASE_ACTIVACION.md](../SUPABASE_ACTIVACION.md).
React no necesita claves de Supabase; utiliza las rutas Auth de Flask.
CLIENTE tiene `/mis-pedidos` y confirmación de compra desde el carrito.
VENDEDOR y ADMINISTRADOR acceden a `/operacion` y `/operacion/ventas`.
Las demás secciones del panel requieren ADMINISTRADOR.

La sesión y el carrito se conservan en `sessionStorage` durante la pestaña.
Cerrar sesión elimina el token y vacía el carrito. Los access/refresh tokens provienen de Supabase Auth y se renuevan antes del
vencimiento. Un 401 intenta renovar una vez cuando corresponde; si Auth rechaza
la renovación, se cierra la sesión. Un fallo de red conserva la sesión; un 403 actualiza los permisos. Flask decide el acceso a cada operación,
aunque alguien cambie el JavaScript o los datos almacenados del navegador.

El tamaño elegido identifica una opción de producto con precio/stock propios.
El total del carrito es estimado: PostgreSQL recalcula el pedido con precios reales.
Los pagos son registros operativos; la aplicación no cobra mediante pasarelas.

Las pruebas de navegador están en `tests/`; instrucciones en `backend/README.md`.

Usuarios y roles tiene búsqueda por correo completo o parcial. Ventas y reportes
solo consultan y muestran el historial después de elegir ambas fechas y pulsar
Consultar. Limpiar fechas oculta resultados y detiene la consulta. Los listados
conservan la paginación de 50 registros y los permisos vigentes de cada rol.
