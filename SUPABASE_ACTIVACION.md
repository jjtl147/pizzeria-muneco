# Activar Supabase Auth y Storage

El código está preparado y probado localmente. El 15 de octubre se confirmó la
aplicación de 003/004 y se verificaron la columna `usuarios.auth_user_id`, el bucket
`productos` y el proveedor Email habilitado con confirmación requerida. Flask ya
se reinició. El estudiante aceptó el flujo operativo de compra, estados,
cobro y permisos al cierre de la jornada. La configuración de URLs/SMTP y las
pruebas específicas de correo, cuentas heredadas y fotos reales siguen pendientes. Para reproducir la instalación, seguir estos pasos. Se requiere
que 001 y 002 ya estén aplicadas; **no volver a ejecutarlas**.

## 1. Migraciones

En el SQL Editor del proyecto Supabase, ejecutar una vez, en este orden:

1. [003_supabase_auth.sql](backend/migrations/003_supabase_auth.sql).
2. [004_imagenes_storage.sql](backend/migrations/004_imagenes_storage.sql).
3. [005_eliminar_rol_heredado.sql](backend/migrations/005_eliminar_rol_heredado.sql).
   Esta limpieza está preparada y probada localmente; su ejecución real todavía
   no está confirmada. Elimina solo la columna antigua `usuarios.rol` y conserva
   `usuarios.roles`. Al terminar debe mostrar `false` para `rol_antiguo_existe`
   y `true` para `roles_vigentes_existen`. No repetir 003/004 si ya se aplicaron.

003 añade `usuarios.auth_user_id` y un trigger para crear perfiles CLIENTE.
Conserva los IDs, roles e historial. No copia los hashes de Werkzeug a Auth:
son formatos distintos. El primer login correcto de una cuenta heredada prueba
la contraseña anterior en Flask y crea la identidad en Auth. El trigger vincula
el perfil mediante `app_metadata.legacy_usuario_id`, escrito exclusivamente por
la API administrativa, y elimina el hash anterior en la misma transacción.

Las identidades importadas se marcan confirmadas como continuidad del acceso
anterior, que no verificaba el correo. **Esto no demuestra titularidad del correo
heredado.** Los registros nuevos sí deben confirmar correo según la configuración
de Auth. Un registro público no puede reclamar un perfil heredado por correo ni
elegir roles. Si ese correo ya existe en Auth sin estar vinculado, el login no
sobrescribe su contraseña: requiere conciliación administrativa de identidades.

Antes de importar cuentas heredadas, deben haber iniciado sesión al menos una
vez para que “Olvidé mi contraseña” tenga una identidad de Auth que recuperar.
Si ya olvidaron su contraseña anterior, se debe verificar la identidad y hacer
una migración asistida; no crear cuentas con el mismo correo para reemplazarlas.

Si 003 falla por correos duplicados sin distinguir mayúsculas/minúsculas,
resolver esos registros antes de continuar. No eliminar perfiles con pedidos.
Un usuario Auth borrado deja el perfil histórico sin acceso; no restaura el hash
ni elimina pedidos. No hay fallback a los JWT anteriores.

004 crea el bucket público `productos` (5 MB, JPEG/PNG/WebP). Las fotos son
públicas porque aparecen en el catálogo. Las cargas pasan por Flask, que exige
ADMINISTRADOR; no se agregan políticas de escritura pública a Storage. Si el
bucket ya existía, revisar en el panel que tenga esos límites y que ninguna
política anterior conceda escrituras a clientes. Las imágenes sustituidas o
subidas sin guardar el producto permanecen en Storage; la limpieza es manual.

## 2. Configurar Authentication

En el panel de Supabase:

1. Habilitar el proveedor **Email** y el registro con contraseña. Mantener
   **Confirm email** activado para los registros nuevos. No habilitar registro
   anónimo ni proveedores sociales en esta fase.
2. En **URL Configuration**, usar como **Site URL**:
   `http://127.0.0.1:5173`.
3. Agregar estas **Redirect URLs** exactas:
   - `http://127.0.0.1:5173/auth/callback`
   - `http://127.0.0.1:5173/restablecer`
4. Mantener las plantillas de confirmación y recuperación con
   `{{ .ConfirmationURL }}`. El flujo preparado recibe las sesiones en el
   fragmento `#` del enlace y lo elimina de la barra tras leerlo.
5. Configurar **SMTP** para enviar confirmaciones y recuperaciones a clientes.
   El correo integrado de Supabase está limitado a direcciones del equipo del
   proyecto y tiene límites de envío; no sirve como correo general de clientes.
   Las credenciales SMTP van en el panel de Supabase, nunca en React o Git.

Al publicar, cambiar Site URL, Redirect URLs y `FRONTEND_URL` al dominio HTTPS
real. Si se utiliza otro puerto/origen en desarrollo, cambiar los tres juntos.
Los límites de Supabase Auth siguen aplicando; al pasar por Flask las solicitudes
comparten la IP del backend. Ajustar los límites en el panel según el despliegue.

## 3. Configuración local y reinicio

En `backend/.env`, conservar `SUPABASE_URL` y `SUPABASE_KEY` e incluir:

```dotenv
FRONTEND_URL=http://127.0.0.1:5173
```

`SUPABASE_KEY` debe ser una clave secreta del servidor (`sb_secret_...` o la
`service_role` heredada), nunca la clave pública. Flask habla con Auth por HTTP
y con PostgreSQL/Storage con su cliente de datos independiente. React no necesita
claves de Supabase. `JWT_SECRET_KEY` deja de utilizarse.

Después de las migraciones, reiniciar Flask desde `backend/`:

```bash
venv/bin/python app.py
```

Iniciar Vite en el origen configurado:

```bash
pnpm --dir frontend dev --host 127.0.0.1 --port 5173 --strictPort
```

Las sesiones anteriores requieren nuevo login. Supabase emite los access/refresh
tokens; React los guarda en `sessionStorage` y renueva la sesión. Flask verifica
la identidad en Auth y vuelve a consultar los roles en cada solicitud protegida.
Cerrar sesión revoca la renovación de la sesión actual; cambiar contraseña pide
revocar la renovación de todas las sesiones. Los access tokens ya emitidos pueden
seguir válidos hasta su vencimiento, según el comportamiento de Supabase.

## 4. Aceptación en el proyecto real

1. Ejecutar `venv/bin/python verificar_supabase.py` desde `backend/`.
2. Iniciar sesión con el administrador existente y su contraseña actual. Verificar
   que aparece en **Authentication → Users**, conserva ID/roles en `usuarios`,
   tiene `auth_user_id` y ya no tiene `password_hash`.
3. Registrar un cliente con un correo accesible, confirmar el correo y comprobar
   que el perfil solo tiene CLIENTE. Revisar entrega y carpeta de spam.
4. Pedir recuperación, abrir el correo, cambiar contraseña y probar login con la
   nueva. Comprobar también un enlace vencido/usado de Supabase.
5. Cerrar sesión y comprobar que las rutas protegidas vuelven al login.
6. Desde Productos, subir una foto y guardar el producto; revisar catálogo y bucket.
7. Repetir compra, estados, cobro y permisos con cuentas cliente/vendedor/admin.
   El pedido #1 permanece sin conciliar; no cancelarlo hasta revisar su stock.

El estudiante confirmó el funcionamiento del flujo operativo del punto 7 al
cierre del 15 de octubre. Esto no acepta por extensión confirmación/recuperación
por correo, fotos reales ni importación de todas las cuentas heredadas, que
siguen pendientes de comprobación específica. Las pruebas locales simulan Auth
y Storage; no comprueban entrega de correo ni configuración del proveedor.

## Otros servicios

Ya se utilizan PostgreSQL, API de datos, funciones RPC y RLS para operaciones
atómicas y permisos. Auth y Storage son las incorporaciones de esta revisión.
Realtime puede evaluarse después para actualizar pedidos sin recargar: requeriría
definir permisos de suscripción; las tablas actuales no permiten lectura directa
de clientes. Telegram y el proveedor LLM siguen siendo servicios externos.

Referencias oficiales: [Auth](https://supabase.com/docs/guides/auth),
[SMTP](https://supabase.com/docs/guides/auth/auth-smtp),
[redirecciones](https://supabase.com/docs/guides/auth/redirect-urls),
[sesiones](https://supabase.com/docs/guides/auth/sessions),
[Storage](https://supabase.com/docs/guides/storage).
