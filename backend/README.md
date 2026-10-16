# Backend de Pizzería Muñeco

## Instalación en una base existente

1. Reactivar el proyecto Supabase si está pausado.
2. Si faltan, aplicar 001 y 002, una vez y en orden. No repetirlas.
3. Aplicar `migrations/003_supabase_auth.sql` y `migrations/004_imagenes_storage.sql`.
   Después aplicar `migrations/005_eliminar_rol_heredado.sql` para retirar `rol`.
4. Configurar Auth, redirecciones y correo siguiendo
   [SUPABASE_ACTIVACION.md](../SUPABASE_ACTIVACION.md).
5. Configurar `.env` desde `.env.example`: URL, clave secreta del servidor y
   `FRONTEND_URL`. No se necesita `JWT_SECRET_KEY` ni claves en React.
6. Iniciar desde `backend/`: `venv/bin/python app.py`. Volver a iniciar sesión.
7. Si no existe administrador, ejecutar `venv/bin/python seed_admin.py`.
   Si ya existe uno, asignar roles desde el panel de usuarios.
8. Comprobar tamaños e inventario. Los pedidos antiguos con
   `stock_descontado=NULL` requieren conciliación antes de cancelarlos.

En una base nueva ejecutar `schema.sql` y después 001, 002, 003, 004 y 005.
No se han ejecutado 003 ni 004 automáticamente en tu proyecto real.

Supabase Auth gestiona credenciales, verificación de correo y sesiones. Flask
valida el access token con Auth y consulta `usuarios.roles` por `auth_user_id` en
cada solicitud. Los roles del JWT o de `user_metadata` no conceden permisos.
Las cuentas heredadas se importan al primer login correcto, conservando ID,
roles y pedidos; el hash local se elimina. La guía explica los límites de correo,
recuperación de cuentas aún no migradas y revocación de sesiones.

Las tablas operativas mantienen RLS y acceso reservado a Flask con su clave
secreta. La migración 005 elimina `usuarios.rol`; `usuarios.roles` conserva
los permisos vigentes. Hasta aplicar 005, `rol` sigue siendo un dato heredado.
Supabase Storage guarda fotos públicas en el bucket `productos`; la ruta
`POST /api/productos/imagen` solo admite ADMINISTRADOR y archivos JPEG/PNG/WebP
hasta 5 MB. La interfaz conserva también la opción de URL de imagen.

## Roles, pedidos y ventas

### Limpieza del esquema

`005_eliminar_rol_heredado.sql` elimina únicamente `usuarios.rol`, con una
transacción, validación de `roles` y sin CASCADE. Si una dependencia externa
impide borrarlo o no se consigue el bloqueo en cinco segundos, se cancela
la operación; no elimina dependencias ni modifica cuentas. La consulta final
debe devolver `rol_antiguo_existe=false` y `roles_vigentes_existen=true`.

Las ocho tablas de la aplicación siguen teniendo uso:

| Tabla | Función vigente |
|---|---|
| `usuarios` | Perfiles, roles y vínculo con Auth; referencias del historial |
| `categorias` | Organización y administración del catálogo |
| `productos` | Opciones vendibles con tamaño y precio propios |
| `inventario` | Stock actual y alertas por producto |
| `pedidos` | Compra, entrega y control de cancelación |
| `detalle_pedidos` | Cantidades y precio/nombre/tamaño históricos |
| `ventas` | Cobros y reportes de ventas |
| `historial_estados` | Registro de cambios de estado del pedido |

`password_hash` sigue siendo necesario para importar cuentas heredadas: no
retirarlo hasta migrarlas todas y reemplazar la lógica de transición de Auth.
`stock_descontado` evita devoluciones incorrectas al cancelar. Los precios,
nombres y tamaños del detalle conservan el historial aunque cambie el catálogo.
No son duplicados descartables. Los esquemas internos `auth` y `storage` son
gestionados por Supabase y no forman parte de esta limpieza.

`schema.sql` y 001–004 conservan su historial de evolución; para crear una base
limpia se ejecuta la cadena completa hasta 005, sin editar ni repetir migraciones
anteriores sobre una base existente. Las funciones que restan la clave JSON
`rol` de sus respuestas siguen siendo compatibles aunque el campo ya no exista.

### Operación

El registro público siempre asigna CLIENTE, aunque la solicitud incluya otros
roles. Cada solicitud protegida vuelve a leer los permisos de la cuenta.
El administrador asigna roles; una cuenta puede combinar los tres.
VENDEDOR gestiona pedidos y ventas, sin acceso a inventario, usuarios o reportes.

### Búsqueda y consultas por fechas

El panel de usuarios permite buscar por correo completo o parte de él, sin
distinguir mayúsculas/minúsculas. `GET /api/usuarios?email=ejemplo&pagina=1`
filtra en PostgreSQL antes de paginar; sin `email` conserva el listado normal.
Se rechazan comodines y espacios; `_` se busca como carácter literal.

El historial de ventas y los reportes empiezan sin resultados ni solicitudes de
datos. Se deben elegir **Desde**, **Hasta** y pulsar **Consultar**. Limpiar fechas
oculta los resultados. El backend también exige ambas fechas, por ejemplo:

```text
GET /api/ventas?desde=2026-10-01&hasta=2026-10-15&pagina=1
GET /api/reportes/ventas?desde=2026-10-01&hasta=2026-10-15
```

Las fechas incluyen ambos días completos en America/La_Paz y admiten hasta 366
días. El historial mantiene páginas de 50 ventas. VENDEDOR solo consulta ventas
registradas por su propia cuenta, incluso con filtros; ADMINISTRADOR consulta
las de todos en el periodo. Un vendedor no puede consultar reportes, administrar
productos/categorías, modificar stock, asignar roles ni usar el asistente.
Una cuenta que tenga ADMINISTRADOR conserva esos permisos aunque también tenga
VENDEDOR. Los pedidos operativos y el catálogo conservan su carga automática.
Las herramientas del asistente mantienen el resumen de siete días.

Estos filtros no requieren cambios de esquema ni una migración SQL nueva.

Un tamaño es una opción vendible con ID, precio e inventario propios. El catálogo
agrupa opciones por nombre y categoría. El detalle del pedido conserva el nombre,
el tamaño y el precio al comprar, aunque el producto cambie posteriormente.

El flujo normal es PENDIENTE → EN_PREPARACION → EN_CAMINO → ENTREGADO.
Se puede cancelar antes de ENTREGADO; la transacción devuelve stock una sola vez.
Pedidos terminales no se reabren. Los cobros se registran sobre pedidos ENTREGADOS
con método EFECTIVO, QR o TARJETA, sin procesar pagos bancarios.
La venta en local hace pedido, descuento de stock y cobro en una sola transacción.
Los reportes agregan ventas cobradas. El consumo refleja productos de pedidos no
cancelados, no ingredientes. Los límites de fechas usan America/La_Paz.

## Integraciones opcionales

Permanecen desactivadas hasta configurarlas en `.env`.

- Telegram: crear bot con BotFather, obtener su token y el ID del chat receptor.
  Configurar `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` y `TELEGRAM_ENABLED=1`.
  Se notifican pedidos nuevos y stock bajo. Un fallo del envío no revierte una
  compra ya confirmada. Los envíos son de mejor esfuerzo, sin cola de reintentos.
- Asistente: la implementación preparada usa OpenAI Responses por HTTP con
  `httpx`. Elegir un modelo que admita function calling; configurar
  `OPENAI_API_KEY`, `OPENAI_MODEL` y `ASSISTANT_ENABLED=1`.
  Solo ADMINISTRADOR puede usarlo. Sus herramientas leen catálogo, inventario y
  reportes de siete días; no modifican registros ni aceptan SQL del modelo.
  Consulta de catálogo/inventario limitada a 100 filas, indicada a la herramienta.
  Para otro proveedor se debe adaptar `integrations.responder_asistente`.

No se enviaron notificaciones ni se consumió la API del LLM durante las pruebas.

## Pruebas

Diagnóstico previo de solo lectura sobre el Supabase configurado:
`venv/bin/python verificar_supabase.py` desde `backend/`.
Comprueba acceso a las tablas y columnas requeridas, cuenta usuarios por rol y
lista hasta 50 IDs de pedidos no terminales cuyo stock sigue sin conciliar.
No muestra claves ni datos personales y no modifica registros. Un resultado
correcto no sustituye la aceptación de compra, cobro y permisos en el navegador.

Desde `backend/`: `venv/bin/python -m unittest discover -s tests -v`.
Las pruebas Python simulan Supabase y servicios externos. Los scripts
`tests/operaciones_atomicas.sql` y `tests/roles_operacion.sql` se ejecutan en una
base de pruebas, después de las migraciones. Revierten sus datos al terminar,
aunque las secuencias pueden avanzar.

Prueba aislada de navegador con Flask real y PostgreSQL PGlite:

```bash
# Desde la raíz del repositorio. Herramientas solo de prueba, fuera del proyecto.
mkdir -p /tmp/muneco-verificacion
pnpm --dir /tmp/muneco-verificacion add @electric-sql/pglite @playwright/test --store-dir /tmp/muneco-pnpm-store
node backend/tests/e2e/sql_check.mjs
backend/venv/bin/python backend/tests/e2e/run.py
```

Requiere Chrome en `/usr/bin/google-chrome`; se puede adaptar la ruta en
`frontend/tests/playwright.config.cjs`. Los servidores de prueba usan los puertos
54329, 5059 y 5179, credenciales ficticias y una base efímera. Se detienen al terminar.
Los logs y trazas quedan en `/tmp/muneco-e2e`.
Esta prueba comprueba React → Axios → Flask → PostgreSQL mediante un adaptador
local de prueba. Incluye migración al primer login, renovación y recuperación
con Auth simulado. No comprueba PostgREST, envío de correo ni Storage real.
`tests/supabase_auth.sql` prueba el trigger en un esquema Auth aislado; no debe
ejecutarse en producción. El runner aplica las migraciones hasta 005 y vuelve
a probar la autorización y vinculación de Auth sin la columna heredada. La
prueba SQL compara los datos antes/después de limpiar para detectar pérdidas.
Compras concurrentes con sesiones independientes y servicios externos siguen
requiriendo validación en el entorno real.

Referencias: [bloqueos PostgreSQL](https://www.postgresql.org/docs/current/explicit-locking.html),
[claves Supabase](https://supabase.com/docs/guides/getting-started/api-keys),
[Telegram Bot API](https://core.telegram.org/bots/api#sendmessage),
[OpenAI Docs: function calling](https://developers.openai.com/api/docs/guides/function-calling).
