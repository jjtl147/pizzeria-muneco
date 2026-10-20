# 3.2.8.2 Diccionario de datos

Modelo vigente del repositorio: `backend/schema.sql` seguido de migraciones
001–005. No es una lectura remota del esquema de producción. No incluye secretos
ni datos personales reales. `SERIAL` crea una columna INTEGER con secuencia.
`TIMESTAMPTZ` equivale a TIMESTAMP WITH TIME ZONE. «Sin valor» indica que no hay
DEFAULT explícito; una columna nullable omitida recibe NULL. Tener DEFAULT no
implica NOT NULL. PK implica unicidad y NOT NULL.

## usuarios

Perfiles de aplicación, permisos y vínculo con Supabase Auth. Nueve columnas.

| Campo | Tipo | Nulo | Claves / restricciones | Predeterminado | Descripción |
|---|---|---|---|---|---|
| id | INTEGER (SERIAL) | No | PK | Secuencia | Identificador interno, preservado al importar cuentas heredadas. |
| nombre | VARCHAR(100) | No | — | Sin valor | Nombre de la persona. |
| email | VARCHAR(150) | No | UNIQUE; índice UNIQUE sobre lower(email) | Sin valor | Correo; la unicidad normalizada impide variantes por mayúsculas. |
| password_hash | VARCHAR(255) | Sí | Solo transición | Sin valor | Hash heredado; se elimina al vincular la identidad con Auth. |
| roles | TEXT[] | No | CHECK: cardinalidad 1–3, valores permitidos, sin elementos NULL | ARRAY['CLIENTE']::TEXT[] | Uno o varios permisos: CLIENTE, VENDEDOR y ADMINISTRADOR. |
| telefono | VARCHAR(20) | Sí | — | Sin valor | Teléfono del perfil. |
| direccion | TEXT | Sí | — | Sin valor | Dirección del perfil. |
| creado_en | TIMESTAMPTZ | Sí | — | CURRENT_TIMESTAMP | Momento de creación del perfil. |
| auth_user_id | UUID | Sí | UNIQUE; FK → auth.users.id; ON DELETE SET NULL | Sin valor | Vínculo opcional con identidad de Supabase. |

La migración 005 elimina `rol`; no es una columna vigente. La aplicación rechaza
roles repetidos; el CHECK del arreglo por sí solo no garantiza elementos únicos.
La función `cambiar_roles` impide retirar el último administrador. La tabla no
almacena contraseñas nuevas: las administra Auth. Un perfil heredado sin vincular
puede conservar temporalmente su hash.

## categorias

Organización del catálogo. Cinco columnas.

| Campo | Tipo | Nulo | Claves / restricciones | Predeterminado | Descripción |
|---|---|---|---|---|---|
| id | INTEGER (SERIAL) | No | PK | Secuencia | Identificador de categoría. |
| nombre | VARCHAR(50) | No | UNIQUE | Sin valor | Nombre de la categoría. |
| descripcion | TEXT | Sí | — | Sin valor | Descripción opcional. |
| activo | BOOLEAN | Sí | — | TRUE | Bandera usada para desactivación lógica. |
| creado_en | TIMESTAMPTZ | Sí | — | CURRENT_TIMESTAMP | Fecha de creación. |

## productos

Opciones vendibles del catálogo; cada tamaño es un producto con ID propio.
Nueve columnas.

| Campo | Tipo | Nulo | Claves / restricciones | Predeterminado | Descripción |
|---|---|---|---|---|---|
| id | INTEGER (SERIAL) | No | PK | Secuencia | Identificador de la opción vendible. |
| categoria_id | INTEGER | Sí | FK → categorias.id; ON DELETE SET NULL | Sin valor | Categoría del producto. |
| nombre | VARCHAR(100) | No | — | Sin valor | Nombre comercial; no es único por sí solo. |
| descripcion | TEXT | Sí | — | Sin valor | Descripción del producto. |
| precio | NUMERIC(10,2) | No | CHECK precio >= 0 | Sin valor | Precio vigente de esta opción. |
| imagen | TEXT | Sí | — | Sin valor | URL de imagen, incluida la URL pública de Storage. |
| activo | BOOLEAN | Sí | — | TRUE | Disponibilidad lógica en catálogo. |
| creado_en | TIMESTAMPTZ | Sí | — | CURRENT_TIMESTAMP | Fecha de creación. |
| tamano | VARCHAR(40) | Sí | — | Sin valor | Tamaño de esta opción; NULL para productos sin tamaño. |

El DDL no impone unicidad de nombre/categoría/tamaño. Agrupar opciones en la
interfaz no crea una tabla adicional de tamaños. El catálogo puede cambiar sin
alterar nombre, tamaño y precio históricos en los detalles ya registrados.

## inventario

Existencias enteras por producto vendible. Cinco columnas.

| Campo | Tipo | Nulo | Claves / restricciones | Predeterminado | Descripción |
|---|---|---|---|---|---|
| id | INTEGER (SERIAL) | No | PK | Secuencia | Identificador de inventario. |
| producto_id | INTEGER | No | UNIQUE; FK → productos.id; ON DELETE CASCADE | Sin valor | Producto controlado; máximo un inventario por producto. |
| stock_actual | INTEGER | No | CHECK stock_actual >= 0 | 0 | Existencias disponibles para pedidos. |
| stock_minimo | INTEGER | No | CHECK stock_minimo >= 0 | 5 | Umbral utilizado para alertas. |
| actualizado_en | TIMESTAMPTZ | Sí | — | CURRENT_TIMESTAMP | Última actualización; las funciones la actualizan al modificar stock. |

La función de creación de productos inserta explícitamente `stock_minimo = 10`,
aunque el DEFAULT de la columna es 5. El ajuste exige el stock esperado para
detectar cambios concurrentes. No se trata de inventario de ingredientes.

## pedidos

Cabecera de compra y seguimiento operativo. Nueve columnas.

| Campo | Tipo | Nulo | Claves / restricciones | Predeterminado | Descripción |
|---|---|---|---|---|---|
| id | INTEGER (SERIAL) | No | PK | Secuencia | Identificador del pedido. |
| usuario_id | INTEGER | Sí | FK → usuarios.id; ON DELETE SET NULL | Sin valor | Cliente que compra; en venta local corresponde al operador. |
| fecha_pedido | TIMESTAMPTZ | Sí | — | CURRENT_TIMESTAMP | Fecha del registro. |
| estado | VARCHAR(30) | No | CHECK: PENDIENTE, EN_PREPARACION, EN_CAMINO, ENTREGADO o CANCELADO | 'PENDIENTE' | Estado del proceso. |
| total | NUMERIC(10,2) | No | CHECK total >= 0 | Sin valor | Total calculado a partir de los detalles por la función SQL. |
| direccion_entrega | TEXT | No | — | Sin valor | Dirección indicada; en venta local se guarda 'Venta en local'. |
| telefono_contacto | VARCHAR(20) | Sí | — | Sin valor | Contacto para este pedido. |
| metodo_pago | VARCHAR(50) | Sí | Sin CHECK propio de métodos en la columna | 'EFECTIVO' | Método indicado o actualizado al registrar el cobro. |
| stock_descontado | BOOLEAN | Sí | — | Sin valor | TRUE: descontó stock; FALSE: sin descuento vigente; NULL: pedido heredado por conciliar. |

Índice adicional: `(usuario_id, fecha_pedido DESC)`. El CHECK de estado valida
valores; la función `cambiar_estado_pedido` controla transiciones y terminales.
Los métodos permitidos se validan en API/funciones y en `ventas.metodo_pago`.
Los pedidos nuevos de la función atómica reciben `stock_descontado = TRUE`.
Cancelar con NULL se bloquea; cancelar con TRUE devuelve stock y deja FALSE.
No existen columnas de nota libre, mesa o reserva estructurada.

## detalle_pedidos

Líneas del pedido e instantáneas de la compra. Ocho columnas.

| Campo | Tipo | Nulo | Claves / restricciones | Predeterminado | Descripción |
|---|---|---|---|---|---|
| id | INTEGER (SERIAL) | No | PK | Secuencia | Identificador de línea. |
| pedido_id | INTEGER | No | FK → pedidos.id; ON DELETE CASCADE | Sin valor | Pedido al que pertenece. |
| producto_id | INTEGER | Sí | FK → productos.id; ON DELETE SET NULL | Sin valor | Opción de producto referenciada. |
| cantidad | INTEGER | No | CHECK cantidad > 0 | Sin valor | Unidades compradas. |
| precio_unitario | NUMERIC(10,2) | No | CHECK precio_unitario >= 0 | Sin valor | Precio vigente al comprar, guardado como dato histórico. |
| subtotal | NUMERIC(10,2) | No | CHECK subtotal >= 0 | Sin valor | Cantidad por precio, calculado en la función de pedido. |
| nombre_producto | TEXT | Sí | Snapshot mediante trigger | Sin valor | Nombre del catálogo al insertar la línea. |
| tamano | TEXT | Sí | Snapshot mediante trigger | Sin valor | Tamaño al insertar la línea. |

El trigger `detalle_snapshot` ejecuta `guardar_tamano_y_nombre_detalle` antes de
insertar. Los CHECK no imponen por sí solos que subtotal sea cantidad × precio;
esa igualdad la calcula la función de creación. No se exige UNIQUE sobre
pedido/producto; la función agrupa productos repetidos antes de insertar.

## ventas

Cobros registrados, con un máximo de una venta por pedido. Seis columnas.

| Campo | Tipo | Nulo | Claves / restricciones | Predeterminado | Descripción |
|---|---|---|---|---|---|
| id | INTEGER (SERIAL) | No | PK | Secuencia | Identificador de venta. |
| pedido_id | INTEGER | No | UNIQUE; FK → pedidos.id; ON DELETE NO ACTION | Sin valor | Pedido cobrado; impide un segundo registro para el mismo pedido. |
| vendedor_id | INTEGER | Sí | FK → usuarios.id; ON DELETE SET NULL | Sin valor | Operador que registra el cobro, vendedor o administrador. |
| fecha_venta | TIMESTAMPTZ | No | — | CURRENT_TIMESTAMP | Momento del registro de cobro. |
| total | NUMERIC(10,2) | No | CHECK total >= 0 | Sin valor | Importe del pedido al cobrar. |
| metodo_pago | TEXT | No | CHECK: EFECTIVO, QR o TARJETA | Sin valor | Método recibido y registrado, sin integración bancaria. |

Índice adicional: `(fecha_venta)`. La función `registrar_venta` exige pedido
ENTREGADO, bloquea la cabecera, comprueba ausencia de venta e inserta el total
del pedido. `venta_directa` realiza todo el flujo local en una transacción.

## historial_estados

Registro de cambios de estado. Seis columnas.

| Campo | Tipo | Nulo | Claves / restricciones | Predeterminado | Descripción |
|---|---|---|---|---|---|
| id | INTEGER (SERIAL) | No | PK | Secuencia | Identificador del cambio. |
| pedido_id | INTEGER | No | FK → pedidos.id; ON DELETE NO ACTION | Sin valor | Pedido afectado. |
| usuario_id | INTEGER | Sí | FK → usuarios.id; ON DELETE SET NULL | Sin valor | Operador que ejecuta el cambio. |
| estado_anterior | TEXT | No | Sin CHECK propio de enumeración | Sin valor | Estado previo. |
| estado_nuevo | TEXT | No | Sin CHECK propio de enumeración | Sin valor | Estado posterior. |
| fecha | TIMESTAMPTZ | No | — | CURRENT_TIMESTAMP | Momento del cambio. |

Las funciones operativas controlan los estados registrados. Solicitar el mismo
estado actual no crea otra fila. La venta local inserta el cambio directo de
PENDIENTE a ENTREGADO dentro de su flujo específico.

## Servicios gestionados y restricciones transversales

- `auth.users` pertenece al esquema gestionado de Supabase. Se muestra su PK UUID
  en el ER únicamente para explicar el vínculo. No se propone modificar su DDL.
- El trigger de la migración 003 crea el perfil del nuevo registro con CLIENTE
  o vincula una cuenta heredada mediante metadatos administrativos verificados.
- Storage gestiona archivos y su esquema interno; el bucket `productos` es
  público y admite JPEG/PNG/WebP hasta 5 MB según la migración 004.
- Las ocho tablas tienen RLS habilitado y acceso operativo reservado al servidor.
  Flask valida los permisos; una clave de servicio no debe enviarse al navegador.
- Las relaciones que no especifican borrado en el DDL utilizan NO ACTION. Los
  flujos de productos y categorías usan desactivación lógica, sin borrar historia.
- Las fechas se almacenan como instantes con zona horaria. Los límites de los
  reportes se interpretan según America/La_Paz.
- Las 57 columnas descritas pertenecen al esquema de la aplicación. No se
  agregan entidades de ingredientes, recetas o roles que el DDL actual no tiene.
