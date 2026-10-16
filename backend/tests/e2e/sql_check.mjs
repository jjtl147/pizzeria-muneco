import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
const herramientas = createRequire((process.env.TEST_TOOLS_PATH || '/tmp/muneco-verificacion') + '/package.json')
const { PGlite } = herramientas('@electric-sql/pglite')
const raiz = new URL('../../', import.meta.url)
const db = new PGlite()
try {
  await db.exec('CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role BYPASSRLS;')
  for (const archivo of ['schema.sql', 'migrations/001_operaciones_atomicas.sql', 'tests/operaciones_atomicas.sql']) {
    await db.exec(await readFile(new URL(archivo, raiz), 'utf8'))
  }
  await db.exec("INSERT INTO usuarios(nombre,email,password_hash,rol) VALUES('Admin previo','previo@test.invalid','hash','ADMINISTRADOR')")
  await db.exec(await readFile(new URL('migrations/002_roles_tamanos_operacion.sql', raiz), 'utf8'))
  const { rows } = await db.query("SELECT roles FROM usuarios WHERE email='previo@test.invalid'")
  if (!rows[0].roles.includes('ADMINISTRADOR')) throw Error('El administrador previo perdió su rol.')
  await db.exec(await readFile(new URL('tests/roles_operacion.sql', raiz), 'utf8'))
  for (const archivo of ['tests/e2e/auth_schema.sql', 'migrations/003_supabase_auth.sql',
    'migrations/004_imagenes_storage.sql', 'tests/supabase_auth.sql']) {
    await db.exec(await readFile(new URL(archivo, raiz), 'utf8'))
  }
  // La limpieza debe conservar exactamente los datos de las ocho tablas,
  // excluyendo únicamente el campo obsoleto que se elimina.
  const tablas = ['usuarios', 'categorias', 'productos', 'inventario', 'pedidos',
    'detalle_pedidos', 'ventas', 'historial_estados']
  async function snapshot() {
    const datos = {}
    for (const tabla of tablas) {
      datos[tabla] = (await db.query(`SELECT to_jsonb(t)-'rol' AS dato FROM ${tabla} t ORDER BY id`)).rows
    }
    return JSON.stringify(datos)
  }
  const antes = await snapshot()
  await db.exec(await readFile(new URL('migrations/005_eliminar_rol_heredado.sql', raiz), 'utf8'))
  if (antes !== await snapshot()) throw Error('La limpieza modificó datos vigentes.')
  const columnas = (await db.query("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='usuarios'")).rows.map(r => r.column_name)
  if (columnas.includes('rol') || !['roles', 'auth_user_id', 'password_hash'].every(c => columnas.includes(c))) {
    throw Error('La limpieza dejó columnas incorrectas.')
  }
  // Probar permisos/último administrador y el trigger de Auth con el esquema limpio.
  for (const archivo of ['tests/roles_operacion.sql', 'tests/supabase_auth.sql']) {
    await db.exec(await readFile(new URL(archivo, raiz), 'utf8'))
  }
  console.log('Migraciones 001–005, limpieza sin pérdida de datos, roles, stock, ventas y Auth: OK')
} finally { await db.close() }
