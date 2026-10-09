# Guía técnica para la defensa — Pizzería Muñeco

## Qué problema resuelve el sistema

Permite al cliente elegir pizzas y tamaños, registrar un pedido y consultar su
estado. El vendedor procesa pedidos y registra ventas y métodos de pago. El
administrador mantiene catálogo, inventario y usuarios, y consulta reportes.
Telegram avisa de pedidos nuevos y stock bajo; el asistente permite consultas
sobre datos operativos cuando se configure el proveedor externo.

## Responsabilidades de cada tecnología

```mermaid
flowchart LR
    Cliente[React y Bootstrap] -->|Axios: JSON y JWT| Flask[Flask: validación y autorización]
    Flask -->|Supabase: tablas y RPC| PostgreSQL[PostgreSQL: datos y transacciones]
    Flask -->|Notificaciones opcionales| Telegram[Telegram]
    Flask -->|Herramientas de lectura| LLM[LLM opcional]
```

React maneja la interacción y el estado visual. Context API conserva sesión y
carrito sin agregar otra librería de estado. Axios hace las solicitudes HTTP.
Flask valida los datos y los permisos. Supabase ofrece el acceso al PostgreSQL
alojado. Las funciones SQL resuelven las escrituras que deben ocurrir juntas.

## Roles combinables y seguridad

`usuarios.roles` guarda un arreglo, por ejemplo `['CLIENTE','VENDEDOR']`.
El decorador `rol_requerido('ADMINISTRADOR','VENDEDOR')` hace una comprobación OR:
basta tener alguno de los roles autorizados. Cada solicitud protegida consulta
los roles vigentes en PostgreSQL, evitando que un token antiguo mantenga un
permiso retirado. Las rutas de React ocultan pantallas; Flask garantiza el acceso.

Las contraseñas se guardan como hashes, no como texto. El token JWT se firma
con una clave del entorno y expira. El registro público no puede elegir roles.
Las tablas tienen RLS y acceso reservado al backend; las claves secretas no
están en el navegador. El último administrador no puede perder ese rol.

## Tamaños, precio y stock

Cada fila de productos representa una opción vendible. Una Margarita Mediana y
una Margarita Familiar tienen IDs diferentes, precio propio e inventario propio.
El catálogo agrupa opciones por nombre/categoría. Esta decisión conserva las
relaciones de inventario y pedido existentes sin añadir un segundo modelo de stock.

El detalle del pedido almacena nombre, tamaño y precio al momento de comprar.
Cambiar luego el nombre o precio del catálogo no altera la evidencia histórica.
El carrito muestra un total estimado: la base recalcula con los precios reales.

## Transacciones y concurrencia

Crear un pedido realiza en una transacción: validación de disponibilidad,
cálculo del total, cabecera, detalles y descuento de stock. Un error revierte
las escrituras. Esto demuestra atomicidad y mantiene la consistencia del negocio.
Los bloqueos por fila serializan compras del mismo producto; se adquieren en
orden de ID para reducir conflictos. Las pruebas aisladas verifican rollback;
la prueba de concurrencia con sesiones independientes se debe hacer en PostgreSQL.

Cancelar bloquea el pedido y devuelve stock una sola vez.
La marca `stock_descontado` impide devolver cantidades que nunca se reservaron.
Los pedidos anteriores requieren conciliación porque su código podía no descontar stock. No se puede reabrir
un pedido cancelado o entregado. Los cambios quedan en `historial_estados`.
La edición de inventario compara el stock que vio el administrador con el vigente:
si cambió por otra operación, se rechaza el ajuste hasta recargar la información.

## Ventas, cobros y reportes

El pedido representa una orden; la venta representa su cobro registrado.
Solo un pedido entregado puede cobrarse y la restricción UNIQUE de ventas.pedido_id
impide dos ventas del mismo pedido. La venta en local crea pedido y cobro juntos.
Se registra EFECTIVO, QR o TARJETA; no se realiza una transacción bancaria.

Los reportes usan ventas registradas, no pedidos pendientes. PostgreSQL agrega
los datos para evitar totales incompletos por límites de listado. Se consulta por
fechas en horario de Bolivia y se muestran productos, tamaños, pagos y ventas diarias.
El consumo semanal representa productos reservados/vendidos en pedidos no cancelados,
no ingredientes: no hay tablas de recetas o materias primas en el alcance actual.

## Asistente y Telegram

El LLM selecciona funciones predefinidas. Flask ejecuta solamente herramientas
autorizadas de lectura y devuelve sus datos para que el modelo redacte la respuesta.
No se ejecuta SQL generado por el modelo ni se le permite modificar permisos.
El acceso es exclusivo del administrador, las llamadas tienen límites y las
claves se configuran en el servidor. La opción preparada usa OpenAI Responses;
la elección del proveedor/modelo y su validación real siguen pendientes.

Telegram envía avisos después de confirmar el pedido. Si falla el envío, no se
pierde una compra. Actualmente es de mejor esfuerzo, sin reintentos persistentes.
Bot, chat y credenciales todavía deben configurarse y probarse.

## Evidencias y límites

- Pruebas Python: validaciones, permisos de los tres roles y sus siete combinaciones,
  revocación de roles con JWT vigente e integraciones simuladas.
- Pruebas SQL: migración de usuarios, atomicidad, stock por tamaño, estados,
  devolución de stock, cobros duplicados y reportes, en PostgreSQL PGlite aislado.
- Prueba de navegador: React, Axios, Flask real y PostgreSQL mediante adaptador local.
  Incluye cliente, vendedor y administrador. No se conecta al Supabase del estudiante.
- Build y ESLint comprueban compilación y reglas de JavaScript; no prueban el negocio.

Para el cierre académico se necesitan también pruebas en Supabase, concurrencia
con sesiones independientes, Telegram/LLM reales, diagramas revisados y aceptación.
El código implementado no equivale a todo el sistema desplegado y aceptado.

## Demostración sugerida

1. Registrarse como cliente, elegir un tamaño y confirmar un pedido.
2. Mostrar detalle y estado del pedido; comprobar stock descontado.
3. Como vendedor, avanzar los estados y registrar el pago al entregar.
4. Registrar una venta en local y mostrarla en el historial.
5. Como administrador, editar producto, ajustar stock y asignar roles combinados.
6. Retirar un rol y demostrar que el token anterior no concede ese permiso.
7. Mostrar reportes de las ventas y pruebas de cancelación/cobro duplicado.
8. Demostrar Telegram y asistente cuando estén configurados; explicar sus límites.
