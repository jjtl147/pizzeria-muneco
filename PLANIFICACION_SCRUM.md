# Planificación Scrum — Sistema Web para Pizzería Muñeco

Proyecto de titulación — Ingeniería de Sistemas.
Inicio: 4 de septiembre de 2026. Entrega objetivo: 10 de noviembre de 2026.
Estado revisado: 9 de octubre de 2026.

## Criterio de avance

Una casilla marcada significa implementación disponible en el repositorio, con
las comprobaciones locales indicadas. El cierre de un sprint requiere además
validación integrada en Supabase y aceptación de sus flujos. No se equipara
código implementado con despliegue o servicio externo operativo.

## Resumen de avance

**Avance del plan actual: 78 % (39 de 50 tareas marcadas).**

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
| Sprint 3 | 9 / 11 | 82 % |
| Sprint 4 | 8 / 9 | 89 % |
| Sprint 5 | 6 / 9 | 67 % |
| Buffer final | 3 / 8 | 38 % |
| **Total** | **39 / 50** | **78 %** |

Las tareas de aceptación pendientes siguen impidiendo el cierre de los sprints
correspondientes, aunque su implementación esté disponible.

| Área | Estado |
|---|---|
| Vistas base, rutas, catálogo y carrito | Implementadas |
| API Flask, Supabase y esquema inicial | Implementados |
| Login, registro, sesión y pedidos del cliente con Axios | Implementados; validar con Supabase |
| Roles combinables y tamaños con precio/stock propios | Migración y código preparados |
| Panel del vendedor: pedidos, ventas y tipo de pago | Implementado; validar con Supabase |
| Panel del administrador: productos, categorías, inventario, usuarios y roles | Implementado; validar con Supabase |
| Reportes de ventas, estadísticas y consumo de productos | Implementados; validar con Supabase |
| Telegram y asistente LLM con herramientas de lectura | Código preparado; faltan credenciales y pruebas con servicios reales |

La conexión por Axios incluye ahora catálogo, autenticación, pedidos y paneles.
Verificación local: 27 pruebas Python, scripts SQL y recorrido completo de navegador
aprobados; ESLint y compilación correctos.

Las pruebas locales no sustituyen la comprobación de las políticas, las claves
ni el esquema del proyecto Supabase del estudiante.

### Qué está hecho y qué falta comprobar

- [x] Panel de administración: productos, categorías, inventario, usuarios y roles.
- [x] Panel de informes/dashboard: indicadores de ventas, filtros, tablas y exportación CSV.
- [x] Interfaz y backend del asistente virtual para el administrador.
- [ ] Configurar el proveedor/modelo y probar respuestas reales del asistente.
- [ ] Configurar Telegram y comprobar las notificaciones reales.
- [ ] Validar los paneles y el flujo de compra con el Supabase del proyecto.

El panel de administración se abre con una cuenta ADMINISTRADOR desde
`/operacion`; sus pestañas incluyen productos, categorías, inventario y usuarios.
El dashboard está en `/operacion/reportes` y el asistente en
`/operacion/asistente`. Estos paneles ya tienen implementación; las tareas
pendientes corresponden a configuración externa y aceptación en el entorno real.

## Decisión de diseño: roles combinables

Se utiliza `usuarios.roles`, un arreglo PostgreSQL con uno o varios valores de
CLIENTE, VENDEDOR y ADMINISTRADOR. La migración copia el rol de cada usuario
existente. La columna antigua `rol` se conserva como dato heredado; el código
nuevo no la utiliza para autorizar.

El JWT incluye una lista de roles. Flask consulta el usuario vigente en cada
solicitud protegida: quitar un rol tiene efecto aunque el JWT no haya expirado.
`rol_requerido(...)` permite el acceso cuando coincide al menos un rol.
Los tokens anteriores con `rol` único requieren iniciar sesión nuevamente.

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
- [ ] Aceptar flujo completo de compra en el entorno real.
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
- [ ] Validar la operación en Supabase con cuentas de cada rol.

## Sprint 5 — 26 de octubre al 7 de noviembre

Objetivo: reportes e integraciones.

- [x] Dashboard de ventas cobradas, cantidad y promedio.
- [x] Reportes por fecha, pago, producto y tamaño; descarga CSV.
- [x] Consumo de productos del periodo (últimos siete días por defecto).
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
- [ ] Completar aceptación de flujos de extremo a extremo en Supabase.
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

**Instalación:** aplicar 001 y 002 en orden; 002 se ejecuta una vez. No volver a
crear las tablas de una base existente. Si 001 ya fue aplicada, ejecutar solo 002.
Las migraciones y las integraciones externas no se ejecutan automáticamente.

## Objetivo futuro — Recuperación de acceso y gestión de credenciales

Objetivo: permitir que un usuario recupere el acceso si olvida su contraseña,
sin exponer contraseñas ni permitir cambios de roles. Se propone como mejora
posterior al alcance actual de los cinco sprints; no se incluye en el 78 %.

- [ ] Agregar “Olvidé mi contraseña” al login y un formulario de recuperación.
- [ ] Configurar un servicio de correo para enviar un enlace de restablecimiento
      al correo registrado, después de verificar su titularidad mediante el enlace.
- [ ] Implementar tokens aleatorios de un solo uso, con vencimiento; almacenar
      su hash y limitar los intentos de recuperación.
- [ ] Permitir definir una contraseña nueva, guardar su hash e invalidar las
      sesiones anteriores después del cambio.
- [ ] Mostrar una respuesta genérica al solicitar recuperación, exista o no
      la cuenta, para evitar revelar correos registrados.
- [ ] Probar enlaces vencidos, usados, alterados y el inicio de sesión posterior.
- [ ] Documentar la recuperación de acceso al correo y a las cuentas de los
      proveedores, y la rotación de claves de Supabase, Telegram y del LLM.

**Cómo recuperar el acceso:** la contraseña original no se puede consultar:
la base guarda un hash. Actualmente no existe recuperación automática por
correo; esta mejora permitirá crear una contraseña nueva mediante un enlace.
Si se olvida también el correo de la cuenta, habrá que verificar la identidad
antes de cambiarlo; ese procedimiento debe definirse como parte de la mejora.

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
