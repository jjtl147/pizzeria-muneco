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
  console.log('Migraciones, usuarios existentes, roles, tamaños, stock, rollback, estados y ventas: OK')
} finally { await db.close() }
