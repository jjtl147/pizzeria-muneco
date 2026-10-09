# Backend de Pizzería Muñeco

## Instalación en una base existente

1. Reactivar el proyecto Supabase si está pausado.
2. Ejecutar `migrations/001_operaciones_atomicas.sql` si todavía no fue aplicada.
3. Ejecutar **una vez** `migrations/002_roles_tamanos_operacion.sql`.
4. Configurar `.env` usando `.env.example`: URL, clave secreta de Supabase y clave
   JWT aleatoria de al menos 32 caracteres. Mantener las claves solo en Flask.
5. Iniciar desde `backend/`: `venv/bin/python app.py`.
6. Iniciar sesión nuevamente: los JWT anteriores con un solo rol ya no sirven.
7. Si no existe administrador, ejecutar `venv/bin/python seed_admin.py`.
   El script pide datos y contraseña sin mostrarlos. Si ya existe uno, utilizar
   el panel de usuarios para dar roles a otras cuentas.
8. Crear o editar las opciones de tamaño y comprobar el inventario real.
9. Si hay pedidos previos pendientes, conciliar su inventario: `stock_descontado`
   queda NULL porque no se sabe si el código anterior reservó stock. Tras revisar
   cada pedido, asignar TRUE si se descontó, o FALSE si nunca se descontó.
   La cancelación de pedidos anteriores queda bloqueada hasta esa revisión.

En una base nueva ejecutar primero `schema.sql`, después 001 y 002.
`schema.sql` es la base inicial; las migraciones completan el esquema actual.
No se han aplicado estos archivos automáticamente a tu Supabase.

La migración 002 activa RLS y reserva el acceso de tablas a Flask con su clave
secreta. Este proyecto usa autenticación propia con JWT, no Supabase Auth.
`usuarios.roles` es la fuente de permisos. `usuarios.rol` solo se conserva para
compatibilidad de datos y no debe editarse para asignar permisos.

## Roles, pedidos y ventas

El registro público siempre asigna CLIENTE, aunque la solicitud incluya otros
roles. Cada solicitud protegida vuelve a leer los permisos de la cuenta.
El administrador asigna roles; una cuenta puede combinar los tres.
VENDEDOR gestiona pedidos y ventas, sin acceso a inventario, usuarios o reportes.

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

Desde `backend/`: `venv/bin/python -m unittest discover -s tests -v`.
Las pruebas Python simulan Supabase y servicios externos. Los scripts
`tests/operaciones_atomicas.sql` y `tests/roles_operacion.sql` se ejecutan en una
base de pruebas, después de las migraciones. Revierten sus datos al terminar,
aunque las secuencias pueden avanzar.

Prueba aislada de navegador con Flask real y PostgreSQL PGlite:

```bash
# Desde la raíz del repositorio. Herramientas solo de prueba, fuera del proyecto.
pnpm --dir /tmp/muneco-verificacion add @electric-sql/pglite @playwright/test --store-dir /tmp/muneco-pnpm-store
node backend/tests/e2e/sql_check.mjs
backend/venv/bin/python backend/tests/e2e/run.py
```

Requiere Chrome en `/usr/bin/google-chrome`; se puede adaptar la ruta en
`frontend/tests/playwright.config.cjs`. Los servidores de prueba usan los puertos
54329, 5059 y 5179, credenciales ficticias y una base efímera. Se detienen al terminar.
Los logs y trazas quedan en `/tmp/muneco-e2e`.
Esta prueba comprueba React → Axios → Flask → PostgreSQL mediante un adaptador
local de prueba. No comprueba PostgREST ni la infraestructura de tu Supabase.
Compras concurrentes con sesiones independientes y servicios externos siguen
requiriendo validación en el entorno real.

Referencias: [bloqueos PostgreSQL](https://www.postgresql.org/docs/current/explicit-locking.html),
[claves Supabase](https://supabase.com/docs/guides/getting-started/api-keys),
[Telegram Bot API](https://core.telegram.org/bots/api#sendmessage),
[OpenAI Docs: function calling](https://developers.openai.com/api/docs/guides/function-calling).
