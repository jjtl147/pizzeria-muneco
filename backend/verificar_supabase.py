"""Diagnóstico de solo lectura previo a la aceptación en Supabase.

Desde backend/: venv/bin/python verificar_supabase.py
No imprime credenciales ni datos personales y no modifica registros.
"""
import os
import sys

import httpx
from postgrest.exceptions import APIError
from supabase import ClientOptions, create_client

import app


def verificar():
    url = os.getenv('SUPABASE_URL', '').strip().split('/rest/v1')[0].rstrip('/')
    key = os.getenv('SUPABASE_KEY', '').strip()
    if not url or not key or 'tu-proyecto' in url:
        print('ERROR: configure SUPABASE_URL y SUPABASE_KEY en backend/.env.')
        return 1
    db = create_client(url, key, options=ClientOptions(
        postgrest_client_timeout=httpx.Timeout(10.0),
        auto_refresh_token=False, persist_session=False,
    ))
    tablas = {
        'categorias': 'id,nombre,activo',
        'productos': 'id,tamano,precio,activo',
        'inventario': 'producto_id,stock_actual,stock_minimo',
        'usuarios': 'id,roles,auth_user_id',
        'pedidos': 'id,estado,stock_descontado',
        'detalle_pedidos': 'id,pedido_id,nombre_producto,tamano',
        'ventas': 'id,pedido_id,vendedor_id,metodo_pago',
        'historial_estados': 'id,pedido_id,estado_anterior,estado_nuevo',
    }
    errores = 0
    for tabla, campos in tablas.items():
        try:
            resultado = db.table(tabla).select(campos, count='exact', head=True).execute()
            print(f'OK {tabla}: {resultado.count} registros; columnas requeridas accesibles.')
        except APIError as error:
            # No imprimir el mensaje del proveedor: podría contener datos privados.
            print(f'ERROR {tabla}: código {error.code}; revise esquema y permisos de la clave.')
            errores += 1
    if errores:
        return 1
    for rol in sorted(app.ROLES):
        resultado = db.table('usuarios').select('id', count='exact', head=True).contains('roles', [rol]).execute()
        print(f'Cuentas con {rol}: {resultado.count}')
    pendientes = db.table('pedidos').select('id', count='exact').is_(
        'stock_descontado', 'null').in_('estado', [
            'PENDIENTE', 'EN_PREPARACION', 'EN_CAMINO',
        ]).order('id').limit(50).execute()
    print(f'Pedidos no terminales por conciliar: {pendientes.count}')
    if pendientes.data:
        print('IDs (hasta 50):', ', '.join(str(p['id']) for p in pendientes.data))
        print('Revise las evidencias de stock antes de asignar stock_descontado.')
    identidades = db.table('usuarios').select('id', count='exact', head=True).is_('auth_user_id', 'null').execute()
    print(f'Perfiles sin vincular a Supabase Auth: {identidades.count}')
    print('Diagnóstico de lectura terminado. La compra, los cobros y los permisos aún requieren aceptación.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(verificar())
    except (httpx.HTTPError, APIError):
        print('ERROR: no se pudo completar la consulta. Revise red, estado del proyecto y credenciales.')
        sys.exit(1)
