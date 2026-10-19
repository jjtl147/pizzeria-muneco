"""Pruebas con sesiones PostgreSQL independientes en un clúster desechable.

No carga .env ni acepta una URL de base de datos. Requiere los binarios de
PostgreSQL (initdb, pg_ctl y psql); consulte --help y backend/README.md.
"""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import tempfile
import time


BACKEND = Path(__file__).resolve().parents[1]


class BaseTemporal:
    def __init__(self, binarios, directorio, biblioteca=None):
        self.binarios = Path(binarios)
        self.directorio = Path(directorio)
        # No heredar PGHOST/PGSERVICE/PGOPTIONS de una base externa.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('PG')}
        self.env.update(PGHOST=directorio, PGPORT='5432', PGUSER='pruebas',
                        PGDATABASE='postgres', PGCONNECT_TIMEOUT='5',
                        PGOPTIONS='-c statement_timeout=10000 -c lock_timeout=8000')
        if biblioteca:
            self.env['LD_LIBRARY_PATH'] = str(Path(biblioteca).resolve())
        self.psql = [str(self.binarios / 'psql'), '-X', '-qAt', '-v', 'ON_ERROR_STOP=1']

    def comando(self, nombre, *args):
        return subprocess.run([str(self.binarios / nombre), *args], env=self.env,
                              capture_output=True, text=True, timeout=30, check=True)

    def sql(self, consulta):
        return subprocess.run(self.psql, input=consulta, env=self.env,
                              capture_output=True, text=True, timeout=15,
                              check=True).stdout.strip()

    def aplicar_esquema(self):
        self.sql('CREATE ROLE anon; CREATE ROLE authenticated; '
                 'CREATE ROLE service_role BYPASSRLS;')
        archivos = ['schema.sql', 'migrations/001_operaciones_atomicas.sql',
                    'migrations/002_roles_tamanos_operacion.sql',
                    'tests/e2e/auth_schema.sql', 'migrations/003_supabase_auth.sql',
                    'migrations/004_imagenes_storage.sql',
                    'migrations/005_eliminar_rol_heredado.sql']
        for archivo in archivos:
            self.sql((BACKEND / archivo).read_text())
        self.sql("INSERT INTO usuarios(nombre,email,roles) VALUES "
                 "('Cliente','cliente@test.invalid',ARRAY['CLIENTE']),"
                 "('Vendedor','vendedor@test.invalid',ARRAY['VENDEDOR']);")

    def competir(self, primera, segunda, confirmar=True, error_esperado=None):
        """La segunda sesión debe bloquearse antes de liberar la primera.

        Se observa pg_stat_activity; no se supone simultaneidad por iniciar dos
        hilos ni se usa una espera fija para dar por demostrado el bloqueo.
        """
        procesos = []
        try:
            for nombre in ('primera', 'segunda'):
                proceso = subprocess.Popen(self.psql, env={**self.env, 'PGAPPNAME': nombre},
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True)
                procesos.append(proceso)
            uno, dos = procesos
            uno.stdin.write('BEGIN; SET LOCAL ROLE service_role; ' + primera + '\n')
            uno.stdin.flush()
            if not select.select([uno.stdout], [], [], 12)[0]:
                raise AssertionError('La primera operación no respondió a tiempo.')
            salida = uno.stdout.readline().strip()
            if not salida:
                raise AssertionError('Falló la primera operación: ' + uno.stderr.read())
            json.loads(salida)

            dos.stdin.write('BEGIN; SET LOCAL ROLE service_role; ' + segunda + ' COMMIT;\n')
            dos.stdin.close()
            dos.stdin = None
            limite = time.monotonic() + 5
            while time.monotonic() < limite:
                bloqueada = self.sql("SELECT count(*) FROM pg_stat_activity "
                                     "WHERE application_name='segunda' "
                                     "AND wait_event_type='Lock'")
                if bloqueada == '1':
                    break
                if dos.poll() is not None:
                    raise AssertionError('La segunda sesión terminó sin esperar el bloqueo.')
                time.sleep(0.02)
            else:
                raise AssertionError('No se observó el bloqueo entre sesiones.')

            _, error_uno = uno.communicate('COMMIT;\n' if confirmar else 'ROLLBACK;\n', timeout=12)
            assert uno.returncode == 0, error_uno
            salida_dos, error_dos = dos.communicate(timeout=12)
            if error_esperado:
                assert dos.returncode != 0 and error_esperado in error_dos, error_dos
            else:
                assert dos.returncode == 0, error_dos
                json.loads(salida_dos)
        finally:
            for proceso in procesos:
                if proceso.poll() is None:
                    proceso.kill()
                proceso.wait(timeout=5)
                for flujo in (proceso.stdin, proceso.stdout, proceso.stderr):
                    if flujo and not flujo.closed:
                        flujo.close()


def compra(producto):
    items = json.dumps([{'producto_id': producto, 'cantidad': 1}])
    return f"SELECT crear_pedido_atomico(1,'Prueba',NULL,'EFECTIVO','{items}');"


def probar(db):
    def producto():
        resultado = db.sql("SELECT crear_producto_con_inventario("
                           "'{\"nombre\":\"Prueba concurrente\",\"precio\":25,\"tamano\":\"Mediana\"}',1);")
        return json.loads(resultado)['id']

    def stock(id_producto):
        return db.sql(f'SELECT stock_actual FROM inventario WHERE producto_id={id_producto}')

    def conteos():
        return db.sql('SELECT (SELECT count(*) FROM pedidos),'
                      '(SELECT count(*) FROM detalle_pedidos)')

    ultimo = producto()
    db.competir(compra(ultimo), compra(ultimo), error_esperado='Stock insuficiente')
    assert stock(ultimo) == '0' and conteos() == '1|1', 'Sobreventa o pedido parcial.'
    print('OK: última unidad; un pedido confirmado y otro rechazado sin datos parciales.')

    revertido = producto()
    db.competir(compra(revertido), compra(revertido), confirmar=False)
    assert stock(revertido) == '0' and conteos() == '2|2', 'Rollback no liberó existencias.'
    print('OK: si la primera compra revierte, la segunda puede usar la unidad disponible.')

    pedido = db.sql(f'SELECT pedido_id FROM detalle_pedidos WHERE producto_id={ultimo}')
    cancelar = f"SELECT cambiar_estado_pedido(2,{pedido},'CANCELADO');"
    db.competir(cancelar, cancelar)
    assert stock(ultimo) == '1', 'Se devolvió stock más de una vez.'
    assert db.sql(f"SELECT count(*) FROM historial_estados WHERE pedido_id={pedido} "
                  "AND estado_nuevo='CANCELADO'") == '1', 'Se duplicó el historial.'
    assert db.sql(f'SELECT estado,stock_descontado FROM pedidos WHERE id={pedido}') == 'CANCELADO|f'
    print('OK: dos cancelaciones devuelven stock una sola vez y generan un cambio de estado.')

    pedido = db.sql(f'SELECT pedido_id FROM detalle_pedidos WHERE producto_id={revertido}')
    for estado in ('EN_PREPARACION', 'EN_CAMINO', 'ENTREGADO'):
        db.sql(f"SELECT cambiar_estado_pedido(2,{pedido},'{estado}');")
    cobrar = f"SELECT registrar_venta(2,{pedido},'QR');"
    db.competir(cobrar, cobrar, error_esperado='La venta ya fue registrada')
    assert db.sql('SELECT count(*),sum(total) FROM ventas') == '1|25.00', 'Cobro duplicado.'
    assert db.sql(f'SELECT metodo_pago FROM pedidos WHERE id={pedido}') == 'QR'
    print('OK: dos cobros simultáneos producen una única venta por el importe correcto.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pg-bin', help='Directorio con initdb, pg_ctl y psql.')
    parser.add_argument('--pg-lib', help='Bibliotecas de PostgreSQL extraídas, si no están instaladas.')
    parser.add_argument('--pg-share', help='Directorio con postgres.bki, si se extrajo un paquete.')
    args = parser.parse_args()
    encontrado = shutil.which('initdb')
    binarios = args.pg_bin or (str(Path(encontrado).parent) if encontrado else None)
    if not binarios or not all((Path(binarios) / x).is_file() for x in ('initdb', 'pg_ctl', 'psql')):
        parser.error('Indique --pg-bin con los binarios de PostgreSQL.')
    with tempfile.TemporaryDirectory(prefix='muneco-concurrencia-') as carpeta:
        db = BaseTemporal(str(Path(binarios).resolve()), carpeta, args.pg_lib)
        datos = str(Path(carpeta) / 'datos')
        extra = ['-L', str(Path(args.pg_share).resolve())] if args.pg_share else []
        db.comando('initdb', '-D', datos, '-U', 'pruebas', '-A', 'trust',
                   '--no-locale', '--encoding=UTF8', *extra)
        # Solo socket Unix privado en el directorio temporal, sin puerto TCP.
        opciones = f"-F -k {carpeta} -c listen_addresses='' -c unix_socket_permissions=0700"
        try:
            registro = Path(carpeta) / 'postgres.log'
            try:
                db.comando('pg_ctl', '-D', datos, '-l', str(registro),
                           '-o', opciones, '-w', 'start')
            except subprocess.CalledProcessError:
                if registro.exists():
                    print(registro.read_text(), flush=True)
                raise
            print(db.sql('SELECT version()'))
            db.aplicar_esquema()
            probar(db)
        finally:
            if (Path(datos) / 'postmaster.pid').exists():
                db.comando('pg_ctl', '-D', datos, '-m', 'immediate', '-w', 'stop')
    print('Pruebas terminadas; clúster temporal eliminado.')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.stderr or error.stdout or str(error)) from error
