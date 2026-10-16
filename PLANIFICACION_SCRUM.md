# Planificación Scrum — Sistema Web para Pizzería Muñeco

Proyecto de titulación — Ingeniería de Sistemas.
Inicio: 4 de septiembre de 2026. Entrega objetivo: 10 de noviembre de 2026.
Estado revisado: 15 de octubre de 2026.

## Criterio de avance

Una casilla marcada significa implementación disponible en el repositorio, con
las comprobaciones locales indicadas. El cierre de un sprint requiere además
validación integrada en Supabase y aceptación de sus flujos. No se equipara
código implementado con despliegue o servicio externo operativo.

## Resumen de avance

**Avance del plan original: 84 % (42 de 50 tareas marcadas; quedan 8).**

Se cuentan únicamente las tareas de los cinco sprints y del buffer final;
el resumen repite tareas y no se cuenta nuevamente. Cada tarea tiene el mismo
peso: este porcentaje mide cumplimiento de la lista, no horas de trabajo ni
porcentaje de funcionalidades validadas en producción. Se respetan las casillas
actuales del documento, incluidas las verificaciones marcadas por el estudiante.
El valor debe recalcularse cuando cambien las tareas o sus estados.

| Etapa | Tareas marcadas / total | Avance |
|---|---|---|
| Sprint 1 | 5 / 5 | 100 % |
| Sprint 2 | 8 / 8 | 100 % |
| Sprint 3 | 10 / 11 | 91 % |
| Sprint 4 | 9 / 9 | 100 % |
| Sprint 5 | 6 / 9 | 67 % |
| Buffer final | 4 / 8 | 50 % |
| **Total** | **42 / 50** | **84 %** |

El estudiante acepta el flujo de compra y operación al cierre del 15 de octubre.
Sprint 4 completado. Sprint 3 conserva pendiente la conciliación del pedido #1;
Sprint 5 y el buffer conservan las verificaciones externas y académicas pendientes.

| Área | Estado |
|---|---|
| Vistas base, rutas, catálogo y carrito | Implementadas |
| API Flask, Supabase y esquema inicial | Implementados |
| Login, sesión y pedidos del cliente con Axios | Flujo operativo aceptado por el estudiante; confirmación/recuperación por correo pendientes |
| Roles combinables y tamaños con precio/stock propios | Implementados; aceptación del flujo informada por el estudiante |
| Panel del vendedor: pedidos, ventas y tipo de pago | Implementado; operación aceptada por el estudiante |
| Panel del administrador: productos, categorías, inventario, usuarios y roles | Implementado; aceptación operativa informada por el estudiante |
| Reportes de ventas, estadísticas y consumo de productos | Implementados; comprobación incluida en el flujo aceptado |
| Telegram y asistente LLM con herramientas de lectura | Código preparado; faltan credenciales y pruebas con servicios reales |

La conexión por Axios incluye ahora catálogo, autenticación, pedidos y paneles.
Verificación local actual: 41 pruebas Python, tres recorridos de navegador
y migraciones 001–005 aprobadas; ESLint y compilación correctos. Login administrativo real en Auth comprobado y
bucket de Storage configurado. La recuperación por correo, las fotos reales y
las comprobaciones específicas de servicios externos siguen pendientes. La
aceptación del flujo operativo fue informada por el estudiante al finalizar el día.

Las pruebas locales no sustituyen la comprobación de las políticas, las claves
ni el esquema del proyecto Supabase del estudiante.

### Evidencias iniciales del 15 de octubre de 2026

Los conteos y pendientes siguientes corresponden al diagnóstico inicial; el
cierre de la jornada y la aceptación posterior se registran después.

- Verificación local repetida: 27 pruebas Python aprobadas; ESLint y compilación
  del frontend correctos.
- Consulta de solo lectura en Supabase: 5 productos, 5 registros de inventario,
  3 usuarios, 2 pedidos y ninguna venta. Las consultas de productos, usuarios y
  pedidos reconocen las columnas de tamaños, roles y `stock_descontado`.
- Hay 1 cuenta con ADMINISTRADOR, 2 con CLIENTE y ninguna con VENDEDOR.
  Falta preparar una cuenta de vendedor para la aceptación de ese rol.
- El pedido **#1** está en un estado no terminal y tiene `stock_descontado=NULL`.
  Debe conciliarse con evidencias antes de cancelar; no se modificó su stock.
- El estudiante no dispone de evidencia del descuento del pedido #1 y decide
  mantenerlo pendiente. La aceptación se realizará con sus cuentas desde el
  navegador, sin crear cuentas ni productos exclusivos de prueba.
- Primera compra comunicada por el estudiante: pedido **#3**, consultado en
  Supabase en estado PENDIENTE, con 2 unidades de Pizza Test a 35 (total 70),
  `stock_descontado=TRUE` y stock actual del producto de 48. Sin tamaño asignado
  ni venta registrada todavía. Falta contrastar el stock previo, comprobar una
  opción con tamaño y completar estados, cobro y aceptación por rol.
- Telegram y asistente siguen desactivados y sin credenciales configuradas.
- Próximo paso: aceptar login, compra, historial, stock, estados y cobro usando
  datos de prueba identificados; después comprobar permisos de los tres roles.

Las consultas iniciales por sí solas no aceptaban la compra. Al cierre de la
jornada, el estudiante confirmó que las pruebas indicadas del flujo de trabajo
funcionan correctamente. Se registra su aceptación funcional en Supabase, con
las limitaciones y pendientes del cierre siguiente. El diagnóstico de lectura
puede repetirse con `backend/verificar_supabase.py`.

### Cierre de jornada — 15 de octubre de 2026

- Aceptación informada por el estudiante del flujo propuesto: compra e historial,
  descuento de stock, estados del pedido, cobro, reportes y cancelación de un
  pedido nuevo, con devolución única de stock y restricción de cobro duplicado.
- Se marcan tres tareas del plan original: aceptación de compra (Sprint 3),
  validación operativa por roles (Sprint 4) y aceptación operativa de extremo a
  extremo (buffer). La fuente de aceptación es la confirmación del estudiante;
  no se adjuntaron capturas ni nuevas trazas de sus pruebas manuales.
- Búsqueda de usuarios por correo y consulta de ventas/reportes solo con fechas
  implementadas. Restricciones del vendedor comprobadas en pruebas automatizadas.
- Comprobaciones locales de esta jornada: 41 pruebas Python, tres recorridos de
  navegador, SQL hasta 005, ESLint y compilación aprobados. Auth/Storage externos
  se distinguen de los servicios simulados en las pruebas locales.
- Avance original: **42/50 (84 %)**. La ampliación Auth/Storage conserva **6/9**;
  el flujo operativo aceptado no demuestra por sí solo entrega de correo,
  recuperación, importación de todas las cuentas ni fotos reales.
- Flask y Vite iniciados por el asistente fueron detenidos. Los procesos de las
  pruebas aisladas finalizaron con sus runners. El estudiante realizará el commit.

**Retomar el 16 de octubre:** confirmar el resultado de 005 en Supabase; revisar
URLs de retorno/SMTP y probar confirmación y recuperación con correo real;
comprobar una foto en Storage; continuar con Telegram/asistente, concurrencia y
documentación. Mantener el pedido #1 bloqueado para cancelar hasta conciliar su
inventario con evidencia. No repetir migraciones ya aplicadas.

### Qué está hecho y qué falta comprobar

- [x] Panel de administración: productos, categorías, inventario, usuarios y roles.
- [x] Panel de informes/dashboard: indicadores de ventas, filtros, tablas y exportación CSV.
- [x] Interfaz y backend del asistente virtual para el administrador.
- [ ] Configurar el proveedor/modelo y probar respuestas reales del asistente.
- [ ] Configurar Telegram y comprobar las notificaciones reales.
- [x] Validar los paneles y el flujo de compra con el Supabase del proyecto (aceptación informada por el estudiante).

El panel de administración se abre con una cuenta ADMINISTRADOR desde
`/operacion`; sus pestañas incluyen productos, categorías, inventario y usuarios.
El dashboard está en `/operacion/reportes` y el asistente en
`/operacion/asistente`. Estos paneles ya tienen implementación; las tareas
pendientes corresponden a configuración externa y aceptación en el entorno real.

## Decisión de diseño: roles combinables

Se utiliza `usuarios.roles`, un arreglo PostgreSQL con uno o varios valores de
CLIENTE, VENDEDOR y ADMINISTRADOR. La migración copia el rol de cada usuario
existente. La migración 005 está preparada para retirar la columna antigua `rol`;
el código actual no la utiliza para autorizar. Su ejecución real sigue pendiente.

Supabase Auth emite el JWT de identidad. Flask lo valida con Auth y consulta
`usuarios.roles` mediante `auth_user_id` en cada solicitud protegida: quitar un
rol tiene efecto aunque el token no haya expirado. `rol_requerido(...)` permite
acceso cuando coincide al menos un rol. Los JWT propios anteriores requieren
iniciar sesión nuevamente. Esta adaptación requiere aplicar 003 antes del reinicio.

| Permiso | CLIENTE | VENDEDOR | ADMINISTRADOR |
|---|---|---|---|
| Consultar catálogo | Sí | Sí | Sí |
| Pedidos personales desde carrito e historial propio | Sí | Con CLIENTE | Con CLIENTE |
| Consultar y cambiar estado de pedidos | No | Sí | Sí |
| Registrar ventas y método de pago | No | Sí | Sí |
| Consultar ventas registradas | No | Propias | Todas |
| Productos, categorías e inventario | No | No | Sí |
| Usuarios y asignación de roles | No | No | Sí |
| Reportes y consumo semanal de productos | No | No | Sí |
| Telegram y asistente | No | No | Sí |

## Fase 0 — Base previa a Scrum

React 19, Vite, pnpm, Bootstrap, React Bootstrap, React Router y Context API.
Catálogo inicial con datos de ejemplo, carrito, Git y migración a Linux.
El backend usa Python, Flask y PostgreSQL mediante Supabase. Se conserva este stack.

## Sprint 1 — 4 al 18 de septiembre

Objetivo: cerrar vistas base del cliente e iniciar backend.

- [x] Home y formulario visual de Login.
- [x] Flask, CORS y entorno virtual.
- [x] Configuración Supabase por variables de entorno.
- [x] Esquema de usuarios, categorías, productos, inventario y pedidos.
- [x] GET /api/productos.

Informe histórico: `INFORME_SPRINT_1.md`.

## Sprint 2 — 18 al 30 de septiembre

Objetivo: API REST de productos, pedidos y autenticación.

- [x] CRUD de productos y desactivación lógica.
- [x] Registro y login con contraseña hash y JWT.
- [x] Perfil e historial del cliente.
- [x] Creación de pedidos.
- [x] Catálogo con Axios; Home también consume productos reales.
- [x] Correcciones: validación, secreto JWT obligatorio y operaciones atómicas.
- [x] Aplicar migración 001 en Supabase (ejecución informada por el estudiante).
- [x] Verificar pedidos e inventario en el Supabase real.

## Sprint 3 — 2 al 14 de octubre

Objetivo: cliente conectado y autorización con roles combinables.
Las correcciones de base cubren la transición después del Sprint 2.

- [x] Login y Registro conectados con Axios.
- [x] Sesión, token, cierre de sesión y rutas protegidas.
- [x] Confirmación de pedido desde carrito e historial propio.
- [x] Preparar migración de roles combinables y usuarios existentes.
- [x] JWT con roles y decorador `rol_requerido(...)`.
- [x] Autorizar VENDEDOR para consultar pedidos y cambiar estados.
- [x] RF-04: selección de tamaño, precio y stock independientes.
- [x] Confirmar ejecución correcta de migración 002 en Supabase.
- [x] Comprobar login de usuarios existentes con los nuevos roles.
- [x] Aceptar flujo completo de compra en el entorno real (confirmado por el estudiante al cierre del 15 de octubre).
- [ ] Conciliar si los pedidos anteriores descontaron stock antes de permitir su cancelación.

## Sprint 4 — 14 al 26 de octubre

Objetivo: gestión operativa del administrador y vendedor.

- [x] `seed_admin.py` para el primer administrador.
- [x] Panel operativo con permisos por rol.
- [x] Productos y categorías: creación, edición y desactivación.
- [x] Inventario por tamaño y alertas de stock bajo.
- [x] Gestión de estados y cancelación con devolución única de stock.
- [x] Panel del vendedor: pedidos, venta en local, registro de cobro y método de pago.
- [x] Gestión de usuarios y asignación/quita de roles.
- [x] Impedir quitar el último administrador y registrar cobros duplicados.
- [x] Validar la operación en Supabase con cuentas de cada rol (aceptación del flujo informada por el estudiante).

## Sprint 5 — 26 de octubre al 7 de noviembre

Objetivo: reportes e integraciones.

- [x] Dashboard de ventas cobradas, cantidad y promedio.
- [x] Reportes por fecha, pago, producto y tamaño; descarga CSV.
- [x] Consumo de productos del periodo seleccionado; siete días en las herramientas del asistente.
- [x] Código de notificaciones Telegram: pedido nuevo y stock bajo.
- [x] Código del asistente con LLM y function calling sobre datos reales.
- [x] Asistente limitado a herramientas de lectura y rol ADMINISTRADOR.
- [ ] Crear bot/chat y configurar/habilitar Telegram.
- [ ] Elegir proveedor/modelo y configurar/habilitar el asistente. Se preparó una
      opción con OpenAI Responses; cambiar proveedor requerirá su adaptador.
- [ ] Comprobar entrega real de notificaciones y respuestas del LLM.

## Buffer final — 7 al 10 de noviembre

La ampliación de roles y el ajuste de fechas dejan tres días de estabilización.

- [x] Pruebas locales de validación y autorización por rol y combinaciones.
- [x] Pruebas SQL aisladas de transacciones, tamaños, estados y ventas.
- [x] Flujo de navegador React → Axios → Flask → PostgreSQL aislado: cliente,
      vendedor, administrador, catálogo, compra, cobros, CRUD, inventario y roles.
- [x] Completar aceptación de flujos operativos de extremo a extremo en Supabase (confirmación del estudiante; integraciones externas se validan aparte).
- [ ] Probar compras simultáneas con conexiones PostgreSQL independientes.
- [ ] Verificar notificaciones y asistente con servicios reales.
- [ ] Revisar documentación académica, diagramas UML y casos de uso.
- [ ] Ensayar la sustentación y registrar evidencias del sistema funcionando.

## Pendientes técnicos y decisiones

**RF-04 resuelto por el estudiante:** cada tamaño tiene precio y stock propios.
Cada fila de `productos` es una opción vendible: por ejemplo, Pizza Margarita
Mediana y Pizza Margarita Familiar tienen IDs distintos. Catálogo agrupa por
nombre/categoría y permite elegir tamaño. Se conserva el modelo de inventario
por producto y se guardan nombre/tamaño/precio en el detalle histórico del pedido.
Los productos existentes sin tamaño conservan su ID y su disponibilidad.

**Pagos:** EFECTIVO, QR y TARJETA son registros del método recibido; el sistema no
procesa pagos bancarios. Un pedido entregado se convierte en venta al registrar
su cobro. Una venta en local crea pedido, detalles, descuento y cobro juntos.

**Consumo semanal:** mide unidades de productos de pedidos no cancelados. No se
ha solicitado ni modelado un inventario de ingredientes o recetas.

**Instalación:** aplicar las migraciones 001 a 005 en orden, sin repetir las ya
aplicadas. No volver a crear las tablas de una base existente. Para la ampliación
Auth/Storage, seguir `SUPABASE_ACTIVACION.md`. Las migraciones y la configuración
del panel no se ejecutan automáticamente.

## Ampliación solicitada — Supabase Auth y Storage

Solicitada el 15 de octubre. Se conserva el indicador del plan original de
**42/50 (84 %)**; esta ampliación se informa aparte y requiere reestimar el trabajo
restante después de la activación real. Código preparado no equivale a servicio
activado.

- [x] Delegar registro, login, validación, renovación y cierre de sesión a Auth.
- [x] Preparar migración 003 para vincular identidades sin cambiar IDs ni roles;
      importar cuentas heredadas tras probar su contraseña y eliminar su hash.
- [x] Implementar recuperación y nueva contraseña con respuestas genéricas;
      probar renovación, enlace inválido y cambio con Auth simulado.
- [x] Preparar bucket y subida de fotos de productos con Supabase Storage,
      autorización ADMINISTRADOR y límite de formato/tamaño.
- [x] Documentar activación, configuración SMTP, redirecciones y límites de sesiones.
- [x] Aplicar 003 y 004 en Supabase y reiniciar Flask con el nuevo código.
      Ejecución informada por el estudiante y verificación remota de
      `usuarios.auth_user_id` y bucket `productos`: público, 5 MB, JPEG/PNG/WebP.
- [ ] Configurar Auth, URLs de retorno y correo SMTP en el panel.
- [ ] Validar migración del administrador, confirmación, recuperación, cierre y
      renovación con Auth real; comprobar enlaces vencidos/usados del proveedor.
- [ ] Validar subida y visualización de fotos con Storage real y los permisos.

Comprobación tras activar las migraciones: Auth por correo habilitado, registro
permitido y confirmación de correo requerida. Flask reiniciado y
`FRONTEND_URL=http://127.0.0.1:5173` configurado. Hay 4 perfiles sin vincular a
Auth antes de su primer login. Las URLs del panel, SMTP y los flujos reales
siguen pendientes de comprobación; no se han enviado correos de prueba.

Diagnóstico posterior del acceso: la cuenta administradora solicitada ya no
aparecía en `usuarios` ni en Auth. Se volvió a crear directamente en Auth con
el perfil generado por el trigger y se asignó ADMINISTRADOR. Se verificaron
login real en Auth, consulta del perfil y acceso a usuarios con respuesta 200.
Esta comprobación del login no demuestra la importación de las otras cuentas
heredadas ni el envío de correos. El flujo de compra/operación fue aceptado
posteriormente por el estudiante al cierre de la jornada.

Limpieza solicitada: 005 elimina únicamente `usuarios.rol`. Las ocho tablas
operativas tienen uso; `password_hash` se mantiene para las cuentas todavía sin
migrar y `stock_descontado` para cancelar sin duplicar inventario. Pruebas SQL
aprobadas con comparación de datos antes/después y validación de roles/Auth
sin el campo antiguo. Aplicación de 005 en Supabase pendiente de confirmación.

Filtros solicitados: búsqueda de usuarios por correo parcial/completo en el
servidor; historial de ventas y reportes requieren Desde/Hasta y consulta
explícita, sin carga inicial de datos. Las ventas mantienen 50 registros por
página y el vendedor solo consulta las registradas por su cuenta. Los permisos
administrativos siguen protegidos en Flask. No se requiere migración SQL nueva.

Las contraseñas se gestionan en Auth una vez migradas. Para recuperar una cuenta
heredada, primero debe haberse vinculado al iniciar sesión con su contraseña
anterior; si ya se olvidó, se requiere verificar identidad y migración asistida.
La importación mantiene la confianza del sistema anterior, que no verificaba el
correo; no prueba titularidad del correo heredado. Los registros nuevos deben
confirmarlo. Supabase puede mantener access tokens válidos hasta su vencimiento,
aunque se revoquen los refresh tokens al cerrar sesión/cambiar contraseña.

Ya utilizamos PostgreSQL, funciones RPC y RLS. Realtime queda para evaluación
posterior; requiere políticas propias de suscripción. Telegram y LLM siguen
requiriendo sus proveedores. No se ha cambiado el alcance a inventario de
ingredientes ni a cobros bancarios.

**Credenciales de servicios externos:** son distintas de la contraseña del
usuario de la pizzería. Si una clave se pierde, se debe recuperar el acceso a
la cuenta del proveedor y consultar o generar una clave nueva con sus mecanismos
oficiales; después actualizar `backend/.env` y reiniciar Flask. Mantener una
copia segura en un gestor de contraseñas, fuera de Git y de la documentación
pública. No pegar claves reales en este archivo.

## Metodología

Scrum adaptado al desarrollo individual: backlog ajustable, revisión por sprint,
evidencias en Git y aceptación de flujos. La nueva planificación mantiene el
10 de noviembre como objetivo; las casillas pendientes determinan el cierre real.
