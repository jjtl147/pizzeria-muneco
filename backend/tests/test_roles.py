import itertools
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import app as backend

class Consulta:
    def __getattr__(self, nombre):
        if nombre == 'execute': return lambda: SimpleNamespace(data=[])
        return lambda *a, **k: self

class DB:
    def table(self, nombre): return Consulta()
    def rpc(self, nombre, args):
        class RPC:
            def execute(self):
                return SimpleNamespace(data={'id': 1, 'stock_actual': 5, 'stock_minimo': 2, 'producto_id': 1,
                    'pedido': {'id': 1, 'estado': 'PENDIENTE', 'total': 10}, 'detalles': []})
        return RPC()

class RolesTests(unittest.TestCase):
    def setUp(self):
        self.usuario = {'id': 1, 'roles': ['CLIENTE'], 'nombre': 'Prueba'}
        self.client = backend.app.test_client()
        for p in [patch.object(backend, 'identidad_supabase', return_value='auth-uuid'),
                  patch.object(backend, 'cargar_usuario', side_effect=lambda _: self.usuario),
                  patch.object(backend, 'get_supabase_client', return_value=DB()),
                  patch.dict(os.environ, {'TELEGRAM_ENABLED': '0', 'ASSISTANT_ENABLED': '0'})]:
            p.start(); self.addCleanup(p.stop)
    def headers(self, roles):
        self.usuario['roles'] = roles
        return {'Authorization': 'Bearer token-supabase-de-prueba'}
    def test_combinaciones_de_roles_en_listados(self):
        permisos = {'/api/pedidos': {'ADMINISTRADOR', 'VENDEDOR'}, '/api/ventas': {'ADMINISTRADOR', 'VENDEDOR'},
            '/api/pedidos/mis-pedidos': {'CLIENTE'}, '/api/inventario': {'ADMINISTRADOR'},
            '/api/admin/productos': {'ADMINISTRADOR'}, '/api/admin/categorias': {'ADMINISTRADOR'},
            '/api/usuarios': {'ADMINISTRADOR'}, '/api/reportes/ventas': {'ADMINISTRADOR'}, '/api/integraciones': {'ADMINISTRADOR'}}
        for cantidad in (1, 2, 3):
            for roles in itertools.combinations(['CLIENTE', 'VENDEDOR', 'ADMINISTRADOR'], cantidad):
                for ruta, permitidos in permisos.items():
                    with self.subTest(roles=roles, ruta=ruta):
                        url = ruta + '?desde=2026-10-01&hasta=2026-10-07' if ruta in ('/api/ventas', '/api/reportes/ventas') else ruta
                        self.assertEqual(self.client.get(url, headers=self.headers(list(roles))).status_code,
                                         200 if set(roles) & permitidos else 403)
    def test_permisos_de_escritura(self):
        rutas = [('POST','/api/productos',{'nombre':'Pizza','precio':10},{'ADMINISTRADOR'}),
            ('POST','/api/categorias',{'nombre':'Pizzas'},{'ADMINISTRADOR'}),
            ('PUT','/api/inventario/1',{'stock_actual':5,'stock_minimo':2},{'ADMINISTRADOR'}),
            ('PUT','/api/usuarios/1/roles',{'roles':['CLIENTE']},{'ADMINISTRADOR'}),
            ('PUT','/api/pedidos/1/estado',{'estado':'EN_PREPARACION'},{'ADMINISTRADOR','VENDEDOR'}),
            ('POST','/api/ventas',{'pedido_id':1,'metodo_pago':'QR'},{'ADMINISTRADOR','VENDEDOR'}),
            ('POST','/api/asistente',{'mensajes':[{'role':'user','content':'Ventas'}]},{'ADMINISTRADOR'}),
            ('POST','/api/pedidos',{'direccion_entrega':'Calle','items':[{'producto_id':1,'cantidad':1}]},{'CLIENTE'})]
        for rol in ['CLIENTE','VENDEDOR','ADMINISTRADOR']:
            for metodo,ruta,datos,permitidos in rutas:
                with self.subTest(rol=rol,ruta=ruta):
                    respuesta=self.client.open(ruta,method=metodo,json=datos,headers=self.headers([rol]))
                    if rol in permitidos:
                        self.assertNotIn(respuesta.status_code,(403,500))
                    else: self.assertEqual(respuesta.status_code,403)
    def test_revocacion_con_token_vigente(self):
        headers=self.headers(['ADMINISTRADOR']); self.usuario['roles']=['CLIENTE']
        self.assertEqual(self.client.get('/api/usuarios',headers=headers).status_code,403)
    def test_usuario_eliminado(self):
        headers=self.headers(['CLIENTE']); self.usuario=None
        self.assertEqual(self.client.get('/api/auth/perfil',headers=headers).status_code,401)
    def test_rango_horario_boliviano(self):
        r=backend.rango_reporte('2026-10-01','2026-10-07')
        self.assertEqual(r['p_desde'],'2026-10-01T00:00:00-04:00')
        self.assertEqual(r['p_hasta'],'2026-10-08T00:00:00-04:00')
        with self.assertRaises(ValueError): backend.rango_reporte('2026-10-09','2026-10-01')
