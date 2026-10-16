// PostgreSQL aislado para pruebas: nunca se conecta a Supabase.
import { readFile } from 'node:fs/promises'
import { createServer } from 'node:http'
import { createRequire } from 'node:module'
const require = createRequire(process.env.TEST_TOOLS_PATH + '/package.json')
const { PGlite } = require('@electric-sql/pglite')
const root = new URL('../../', import.meta.url)
const db = new PGlite()
await db.exec('CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role BYPASSRLS;')
for (const archivo of ['schema.sql', 'migrations/001_operaciones_atomicas.sql', 'migrations/002_roles_tamanos_operacion.sql',
  'tests/e2e/auth_schema.sql', 'migrations/003_supabase_auth.sql', 'migrations/004_imagenes_storage.sql',
  'migrations/005_eliminar_rol_heredado.sql']) {
  await db.exec(await readFile(new URL(archivo, root), 'utf8'))
}
await db.exec('SET ROLE service_role;')
createServer(async (req, res) => {
  if (req.method !== 'POST' || req.url !== '/sql') { res.writeHead(404); res.end(); return }
  let body = ''
  for await (const fragmento of req) body += fragmento
  try {
    const { sql, params = [] } = JSON.parse(body)
    const resultado = await db.query(sql, params)
    res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(resultado))
  } catch (error) {
    res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ code: error.code, message: error.message }))
  }
}).listen(54329, '127.0.0.1', () => console.log('PostgreSQL de pruebas: 54329'))
