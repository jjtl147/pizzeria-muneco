# 3.2.6.2 Especificaciones detalladas de casos de uso

Versión documental basada en código al 20 de octubre de 2026. Los nombres
corresponden a los cinco diagramas de casos de uso; los códigos identifican las fichas.
«Disponible» describe código,
no aceptación automática de todas las integraciones externas.

Regla transversal: Flask valida las identidades con Auth y consulta los roles
vigentes; una cuenta puede combinar CLIENTE, VENDEDOR y ADMINISTRADOR.

No se inventan equivalencias CU–HU: la correspondencia con las historias del ODT
debe revisarse al actualizar ese documento y su alcance pendiente.

## CU-01: Registrarse

| Campo | Especificación |
|---|---|
| Actor principal | Persona sin cuenta |
| Objetivo | Solicitar una cuenta de cliente. |
| Precondiciones | Correo, nombre y contraseña válidos; Auth configurado. |
| Flujo principal | 1. Abrir Registro y completar datos.<br>2. Flask valida los campos y solicita el alta a Auth.<br>3. Auth crea la identidad y el trigger crea el perfil con CLIENTE cuando corresponde.<br>4. El sistema muestra una respuesta genérica y solicita revisar el correo.<br>5. La persona confirma el correo mediante el enlace recibido antes de iniciar sesión. |
| Alternativas y excepciones | Datos inválidos: rechazar. Correo ya registrado: mantener respuesta genérica. Error del proveedor: informar sin mostrar credenciales. |
| Postcondiciones | Si el alta procede, identidad y perfil creados; la confirmación habilita el acceso. El registro no inicia una sesión operativa. |
| Evidencia en el código | POST /api/auth/registro; migración 003; Registro.jsx |

## CU-02: Iniciar sesión

| Campo | Especificación |
|---|---|
| Actor principal | Persona con cuenta |
| Objetivo | Acceder a las funciones permitidas por sus roles. |
| Precondiciones | Cuenta confirmada y credenciales válidas; para una cuenta heredada, posibilidad de acreditar su contraseña anterior. |
| Flujo principal | 1. Introducir correo y contraseña.<br>2. Flask valida datos y solicita autenticación a Auth.<br>3. Flask obtiene el perfil y los roles vigentes.<br>4. La interfaz guarda access token, refresh token y expiración en sessionStorage.<br>5. Mostrar las opciones de la cuenta. |
| Alternativas y excepciones | Credenciales inválidas o correo sin confirmar: rechazar. Cuenta heredada sin vínculo: verificar hash anterior, crear identidad mediante API administrativa, conservar ID/roles y reintentar. Fallo del proveedor: informar indisponibilidad. |
| Postcondiciones | Sesión disponible en el navegador y perfil identificado. |
| Evidencia en el código | POST /api/auth/login; auth_supabase.py; api.js |

## CU-03: Recuperar contraseña

| Campo | Especificación |
|---|---|
| Actor principal | Persona que solicita recuperar su cuenta |
| Objetivo | Establecer una contraseña nueva mediante un enlace de recuperación. |
| Precondiciones | Correo con formato válido; cuenta vinculada a Auth para recuperación normal; acceso al correo. |
| Flujo principal | 1. Solicitar recuperación con el correo.<br>2. Flask solicita a Auth el envío y devuelve una respuesta genérica.<br>3. Abrir el enlace y establecer una sesión de recuperación.<br>4. Introducir la contraseña nueva.<br>5. Flask solicita el cambio a Auth y la interfaz termina el flujo de recuperación. |
| Alternativas y excepciones | Enlace inválido, vencido o usado: no permitir completar el flujo y solicitar uno nuevo. Contraseña inválida: pedir corrección. Cuenta heredada sin vincular: requiere migración previa o asistencia verificada. |
| Postcondiciones | Si el enlace y la solicitud son válidos, contraseña actualizada en Auth. |
| Evidencia en el código | POST /api/auth/recuperar; PUT /api/auth/password; Recuperar.jsx; ConfirmarAcceso.jsx |

## CU-04: Cerrar sesión

| Campo | Especificación |
|---|---|
| Actor principal | Cliente, vendedor o administrador |
| Objetivo | Finalizar la sesión de trabajo del navegador. |
| Precondiciones | Sesión iniciada. |
| Flujo principal | 1. Solicitar salir.<br>2. La aplicación solicita el cierre a Flask.<br>3. Flask solicita revocación del alcance local a Auth.<br>4. La interfaz elimina inmediatamente la sesión local y vacía el carrito, mientras la solicitud de revocación se procesa en segundo plano. |
| Alternativas y excepciones | El access token puede seguir siendo aceptado por Auth hasta su vencimiento; esto no implica borrado instantáneo de tokens ya emitidos. La interfaz debe retirar su sesión local. |
| Postcondiciones | Sesión local retirada; revocación del proveedor según resultado de la solicitud. |
| Evidencia en el código | POST /api/auth/logout; AuthProvider.jsx; api.js |

## CU-05: Consultar catálogo

| Campo | Especificación |
|---|---|
| Actor principal | Visitante o persona autenticada |
| Objetivo | Conocer productos disponibles, tamaños y precios. |
| Precondiciones | API disponible. |
| Flujo principal | 1. Abrir catálogo.<br>2. La interfaz solicita productos.<br>3. La API devuelve productos activos e información de stock.<br>4. Mostrar opciones agrupadas por nombre/categoría y sus tamaños.<br>5. Revisar el producto y su disponibilidad. |
| Alternativas y excepciones | Sin productos: mostrar estado vacío. Fallo de red/API: mostrar error y permitir reintentar. |
| Postcondiciones | Catálogo consultado sin cambios en los datos. |
| Evidencia en el código | GET /api/productos; Catalogo.jsx; useProductos.js |

## CU-06: Gestionar carrito

| Campo | Especificación |
|---|---|
| Actor principal | Visitante o cliente |
| Objetivo | Preparar la selección de compra. |
| Precondiciones | Productos consultables en el catálogo. |
| Flujo principal | 1. Seleccionar producto, tamaño y cantidad.<br>2. Agregar la opción al carrito.<br>3. Revisar importes estimados.<br>4. Modificar cantidades o retirar opciones. |
| Alternativas y excepciones | Cantidad no entera o menor a uno: no aplicar la modificación. La disponibilidad y los precios definitivos se verifican al confirmar en el servidor; el carrito no reserva existencias. |
| Postcondiciones | Carrito actualizado en el navegador; sin reserva ni descuento de stock. |
| Evidencia en el código | CartContext.jsx; ProductCard.jsx; CarritoVista.jsx |

## CU-07: Realizar pedido

| Campo | Especificación |
|---|---|
| Actor principal | Cliente |
| Objetivo | Confirmar la compra del carrito. |
| Precondiciones | Sesión válida con CLIENTE; carrito no vacío; dirección y datos válidos. |
| Flujo principal | 1. Revisar carrito y completar datos de entrega.<br>2. Enviar confirmación.<br>3. Flask valida identidad, rol e ítems.<br>4. La función SQL agrupa ítems, bloquea filas y valida disponibilidad.<br>5. Crear pedido y detalles con precios del servidor y descontar existencias en una transacción.<br>6. Devolver pedido PENDIENTE y mostrar confirmación; vaciar carrito. |
| Alternativas y excepciones | Token o rol inválido: 401/403 sin crear pedido. Datos inválidos: 400. Producto inactivo o stock insuficiente: revertir todos los cambios y mantener el carrito. Fallo de notificación opcional: no revierte una compra confirmada. |
| Postcondiciones | Pedido y detalles persistidos; stock descontado y stock_descontado TRUE. No se crea una venta cobrada. |
| Evidencia en el código | POST /api/pedidos; crear_pedido_atomico; Carrito.jsx |

## CU-08: Consultar historial propio

| Campo | Especificación |
|---|---|
| Actor principal | Cliente |
| Objetivo | Revisar sus pedidos y estados. |
| Precondiciones | Sesión válida con CLIENTE. |
| Flujo principal | 1. Abrir Mis pedidos.<br>2. Flask identifica al usuario desde su sesión.<br>3. Consultar solo sus pedidos.<br>4. Mostrar detalles y estados. |
| Alternativas y excepciones | Sin pedidos: mostrar listado vacío. Sesión inválida: solicitar acceso. No permitir consultar historial ajeno usando un ID enviado por el cliente. |
| Postcondiciones | Historial propio consultado sin modificaciones. |
| Evidencia en el código | GET /api/pedidos/mis-pedidos; MisPedidos.jsx |

## CU-09: Consultar pedidos

| Campo | Especificación |
|---|---|
| Actor principal | Vendedor o administrador |
| Objetivo | Identificar pedidos para su atención. |
| Precondiciones | Sesión válida con VENDEDOR o ADMINISTRADOR. |
| Flujo principal | 1. Abrir panel de pedidos.<br>2. La API comprueba el rol operativo.<br>3. Consultar pedidos y mostrar datos operativos.<br>4. Elegir un pedido para revisar sus detalles. |
| Alternativas y excepciones | Sin pedidos: lista vacía. Sin permiso: rechazar solicitud. |
| Postcondiciones | Pedidos consultados sin alterar estados ni stock. |
| Evidencia en el código | GET /api/pedidos; admin/Pedidos.jsx |

## CU-10: Actualizar estado

| Campo | Especificación |
|---|---|
| Actor principal | Vendedor o administrador |
| Objetivo | Registrar avance de preparación y entrega. |
| Precondiciones | Rol operativo; pedido existente; siguiente estado permitido. |
| Flujo principal | 1. Elegir pedido y estado siguiente.<br>2. Flask valida solicitud.<br>3. La función SQL bloquea el pedido y valida la transición.<br>4. Actualizar estado e insertar historial en una transacción.<br>5. Mostrar resultado. |
| Alternativas y excepciones | Mismo estado: devolver pedido sin duplicar historial. Salto no permitido o reapertura de terminal: rechazar. La cancelación se especifica en CU-11. |
| Postcondiciones | Estado actualizado y cambio auditado; el flujo normal no registra cobro. |
| Evidencia en el código | PUT /api/pedidos/{id}/estado; cambiar_estado_pedido |

## CU-11: Cancelar pedido

| Campo | Especificación |
|---|---|
| Actor principal | Vendedor o administrador |
| Objetivo | Anular un pedido y restituir el stock que se hubiera descontado. |
| Precondiciones | Rol operativo; pedido previo a ENTREGADO; stock_descontado conciliado. |
| Flujo principal | 1. Solicitar CANCELADO.<br>2. La función SQL bloquea y valida el pedido.<br>3. Si stock_descontado es TRUE, restituir cantidades referenciadas por los detalles.<br>4. Actualizar CANCELADO y stock_descontado FALSE e insertar historial.<br>5. Confirmar la transacción y mostrar resultado. |
| Alternativas y excepciones | Pedido ya CANCELADO: respuesta sin nueva devolución. ENTREGADO: rechazar. stock_descontado NULL: exigir conciliación previa. Error al devolver stock: revertir toda la operación. |
| Postcondiciones | Pedido cancelado y existencias restituidas como máximo una vez por la operación. |
| Evidencia en el código | PUT /api/pedidos/{id}/estado; cambiar_estado_pedido |

## CU-12: Registrar cobro de pedido

| Campo | Especificación |
|---|---|
| Actor principal | Vendedor o administrador |
| Objetivo | Registrar el pago recibido por un pedido entregado. |
| Precondiciones | Rol operativo; pedido ENTREGADO sin venta previa; método EFECTIVO, QR o TARJETA. |
| Flujo principal | 1. Seleccionar pedido e indicar método recibido.<br>2. Flask valida la solicitud.<br>3. La función SQL bloquea el pedido y comprueba estado y ausencia de venta.<br>4. Insertar venta con total del pedido y operador; actualizar método del pedido.<br>5. Confirmar y mostrar el cobro. |
| Alternativas y excepciones | Pedido no entregado, método inválido o venta existente: rechazar sin cambios. La restricción UNIQUE impide otra venta para el mismo pedido. |
| Postcondiciones | Una venta registrada; sin procesamiento bancario ni nuevo descuento de existencias. |
| Evidencia en el código | POST /api/ventas con pedido_id; registrar_venta |

## CU-13: Registrar venta en local

| Campo | Especificación |
|---|---|
| Actor principal | Vendedor o administrador |
| Objetivo | Registrar una compra atendida en el local en una operación. |
| Precondiciones | Rol operativo; productos y cantidades válidos; método de pago permitido. |
| Flujo principal | 1. Seleccionar productos, cantidades y método recibido.<br>2. Enviar venta sin pedido_id.<br>3. venta_directa crea pedido y detalles, validando y descontando stock.<br>4. Marcar ENTREGADO y registrar historial.<br>5. Registrar el cobro y confirmar todos los cambios juntos. |
| Alternativas y excepciones | Stock insuficiente, producto inactivo o fallo de cobro: revertir pedido, detalles, stock, historial y venta. |
| Postcondiciones | Pedido ENTREGADO y venta creados atómicamente. El usuario del pedido es el operador; dirección: Venta en local. |
| Evidencia en el código | POST /api/ventas sin pedido_id; venta_directa; admin/Ventas.jsx |

## CU-14: Consultar ventas

| Campo | Especificación |
|---|---|
| Actor principal | Vendedor o administrador |
| Objetivo | Revisar cobros registrados en un intervalo. |
| Precondiciones | Rol operativo; Desde y Hasta válidos, con intervalo máximo de 366 días. |
| Flujo principal | 1. Elegir fechas y pulsar Consultar.<br>2. La API convierte los límites según America/La_Paz.<br>3. Para vendedor, filtrar por su usuario; para administrador, incluir todos.<br>4. Mostrar resultados paginados de 50 ventas. |
| Alternativas y excepciones | Fechas ausentes o inválidas: rechazar. Sin resultados: lista vacía. No se cargan ventas antes de la consulta explícita. |
| Postcondiciones | Ventas consultadas con alcance de permisos aplicado. |
| Evidencia en el código | GET /api/ventas; admin/Ventas.jsx |

## CU-15: Gestionar productos

| Campo | Especificación |
|---|---|
| Actor principal | Administrador |
| Objetivo | Crear, editar y desactivar opciones vendibles. |
| Precondiciones | ADMINISTRADOR; datos válidos de producto y categoría cuando se indique. |
| Flujo principal | 1. Consultar productos administrativos.<br>2. Elegir crear o editar e introducir nombre, precio, tamaño y demás datos.<br>3. Validar y guardar; en creación, generar inventario mediante la función SQL.<br>4. Para retirar una opción, aplicar desactivación lógica.<br>5. Mostrar catálogo actualizado. |
| Alternativas y excepciones | Precio o stock inicial negativos, referencias inválidas o datos incompletos: rechazar. La desactivación conserva referencias históricas. |
| Postcondiciones | Producto creado, actualizado o desactivado; cada tamaño conserva ID propio. |
| Evidencia en el código | GET /api/admin/productos; POST/PUT/DELETE /api/productos; admin/Productos.jsx |

## CU-16: Gestionar categorías

| Campo | Especificación |
|---|---|
| Actor principal | Administrador |
| Objetivo | Organizar y mantener las categorías del catálogo. |
| Precondiciones | ADMINISTRADOR; nombre válido y único. |
| Flujo principal | 1. Consultar categorías administrativas.<br>2. Crear o editar nombre y descripción, o solicitar desactivación.<br>3. Validar y guardar la operación.<br>4. Mostrar resultados actualizados. |
| Alternativas y excepciones | Nombre vacío o duplicado: rechazar. Sin permiso: rechazar. |
| Postcondiciones | Categoría creada, editada o desactivada lógicamente. |
| Evidencia en el código | GET /api/admin/categorias; POST/PUT/DELETE /api/categorias; admin/Categorias.jsx |

## CU-17: Consultar y ajustar inventario

| Campo | Especificación |
|---|---|
| Actor principal | Administrador |
| Objetivo | Mantener existencias y mínimos de productos. |
| Precondiciones | ADMINISTRADOR; producto existente; stock y mínimo enteros no negativos. |
| Flujo principal | 1. Consultar inventario y alertas de stock bajo.<br>2. Indicar existencias y mínimo nuevos.<br>3. Enviar también el stock observado anteriormente.<br>4. La función SQL bloquea el registro y compara el valor esperado.<br>5. Guardar ajuste y fecha de actualización. |
| Alternativas y excepciones | El stock cambió desde la lectura: rechazar y pedir recargar. Valores negativos: rechazar. El inventario de ingredientes no forma parte del código actual. |
| Postcondiciones | Inventario de la opción de producto actualizado sin sobrescribir silenciosamente un cambio concurrente. |
| Evidencia en el código | GET /api/inventario; PUT /api/inventario/{producto_id}; ajustar_inventario |

## CU-18: Consultar usuarios

| Campo | Especificación |
|---|---|
| Actor principal | Administrador |
| Objetivo | Localizar cuentas y revisar sus roles. |
| Precondiciones | ADMINISTRADOR. |
| Flujo principal | 1. Abrir usuarios.<br>2. Introducir opcionalmente correo completo o parcial.<br>3. La API filtra en PostgreSQL antes de paginar.<br>4. Mostrar perfiles y roles sin contraseñas. |
| Alternativas y excepciones | Filtro inválido o comodines no admitidos: rechazar. Sin coincidencias: lista vacía. |
| Postcondiciones | Usuarios consultados sin cambios de permisos. |
| Evidencia en el código | GET /api/usuarios; admin/Usuarios.jsx |

## CU-19: Asignar o retirar roles

| Campo | Especificación |
|---|---|
| Actor principal | Administrador |
| Objetivo | Actualizar permisos de una cuenta. |
| Precondiciones | ADMINISTRADOR; usuario existente; uno o varios roles permitidos sin repetidos. |
| Flujo principal | 1. Seleccionar usuario y combinación de roles.<br>2. Enviar cambio.<br>3. Flask y la función SQL validan autorización y roles.<br>4. Comprobar que no se quite el último administrador.<br>5. Guardar y mostrar resultado. |
| Alternativas y excepciones | Lista vacía, roles desconocidos o repetidos: rechazar. Retiro del último administrador: rechazar. Los permisos vigentes se releen en solicitudes posteriores. |
| Postcondiciones | Roles actualizados conservando al menos un administrador. |
| Evidencia en el código | PUT /api/usuarios/{id}/roles; cambiar_roles |

## CU-20: Subir imagen de producto

| Campo | Especificación |
|---|---|
| Actor principal | Administrador |
| Objetivo | Obtener una URL pública para la foto del producto. |
| Precondiciones | ADMINISTRADOR; bucket productos configurado; JPEG, PNG o WebP de hasta 5 MB. Prueba externa de subida pendiente. |
| Flujo principal | 1. Seleccionar archivo.<br>2. Enviar imagen al backend.<br>3. Flask valida permisos, formato y tamaño.<br>4. Subir a Storage y devolver URL pública.<br>5. Usar la URL al guardar el producto mediante CU-15. |
| Alternativas y excepciones | Tipo/tamaño inválido: rechazar. Fallo de Storage: informar sin afirmar que la foto quedó guardada. Subir el archivo no equivale por sí solo a guardar el producto. |
| Postcondiciones | Si Storage acepta la carga, archivo disponible y URL devuelta; vinculación al producto al guardar sus datos. |
| Evidencia en el código | POST /api/productos/imagen; migración 004; admin/Productos.jsx |

## CU-21: Consultar reportes de ventas

| Campo | Especificación |
|---|---|
| Actor principal | Administrador |
| Objetivo | Analizar ventas cobradas por periodo y sus desgloses. |
| Precondiciones | ADMINISTRADOR; Desde/Hasta válidos, máximo 366 días. |
| Flujo principal | 1. Elegir fechas y pulsar Consultar.<br>2. Flask valida y construye el intervalo.<br>3. La función reporte_ventas agrega ventas cobradas y desgloses.<br>4. Mostrar indicadores y tablas por pago y producto/tamaño. |
| Alternativas y excepciones | Sin ventas: mostrar indicadores y tablas sin datos según respuesta. Fechas inválidas: rechazar. No se consulta al abrir la pantalla sin fechas. |
| Postcondiciones | Reporte mostrado sin modificar registros. |
| Evidencia en el código | GET /api/reportes/ventas; reporte_ventas; admin/Reportes.jsx |

## CU-22: Consultar consumo de productos

| Campo | Especificación |
|---|---|
| Actor principal | Administrador |
| Objetivo | Revisar unidades de productos de pedidos no cancelados. |
| Precondiciones | ADMINISTRADOR; periodo de consulta válido. |
| Flujo principal | 1. Consultar el periodo en Reportes.<br>2. La función SQL agrega cantidades de pedidos no cancelados.<br>3. Mostrar unidades por producto y tamaño. |
| Alternativas y excepciones | Sin pedidos: tabla vacía. No interpretar las unidades como ingredientes consumidos ni como ventas ya cobradas. |
| Postcondiciones | Consumo de productos mostrado; sin cambios de existencias. |
| Evidencia en el código | GET /api/reportes/ventas, sección consumo; reporte_ventas |

## CU-23: Exportar ventas por producto a CSV

| Campo | Especificación |
|---|---|
| Actor principal | Administrador |
| Objetivo | Descargar el desglose de ventas por producto y tamaño. |
| Precondiciones | Acceso autorizado a Reportes y resultados de una consulta disponibles. |
| Flujo principal | 1. Consultar el reporte del periodo.<br>2. Pulsar Descargar CSV.<br>3. El navegador convierte las filas de ventas por producto en CSV.<br>4. Descargar ventas-productos.csv. |
| Alternativas y excepciones | Sin resultados: no hay filas de detalle para exportar. La exportación usa los resultados consultados; no es un endpoint adicional de la API. |
| Postcondiciones | Archivo CSV generado localmente sin modificar la base. |
| Evidencia en el código | admin/Reportes.jsx, función exportar |
