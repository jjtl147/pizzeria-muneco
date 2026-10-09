import datetime
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jwt
from postgrest.exceptions import APIError
import app as backend


class BackendTests(unittest.TestCase):
    def setUp(self):
        integraciones = patch.dict(os.environ, {'TELEGRAM_ENABLED': '0', 'ASSISTANT_ENABLED': '0'})
        integraciones.start()
        self.addCleanup(integraciones.stop)
        self.secret = 'clave-aleatoria-exclusiva-para-las-pruebas-locales'
        self.key_patch = patch.object(backend, 'JWT_SECRET_KEY', self.secret)
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)
        self.db = MagicMock()
        self.db_patch = patch.object(backend, 'get_supabase_client', return_value=self.db)
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.usuario = {'id': 1, 'nombre': 'Cliente', 'email': 'cliente@example.test', 'roles': ['CLIENTE']}
        self.usuario_patch = patch.object(backend, 'cargar_usuario', side_effect=lambda _: self.usuario)
        self.usuario_patch.start()
        self.addCleanup(self.usuario_patch.stop)
        self.client = backend.app.test_client()

    def headers(self, rol='CLIENTE', **claims):
        payload = {
            'usuario_id': 1, 'roles': [rol] if isinstance(rol, str) else rol,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
        }
        self.usuario['roles'] = list(payload['roles'])
        payload.update(claims)
        return {'Authorization': 'Bearer ' + jwt.encode(payload, self.secret, algorithm='HS256')}

    def pedido(self, **campos):
        data = {'direccion_entrega': 'Calle 1', 'items': [{'producto_id': 2, 'cantidad': 1}]}
        data.update(campos)
        return self.client.post('/api/pedidos', json=data, headers=self.headers())

    def test_rutas_protegidas_y_rol(self):
        for ruta in ['/api/pedidos', '/api/pedidos/mis-pedidos', '/api/auth/perfil']:
            self.assertEqual(self.client.get(ruta).status_code, 401)
        self.assertEqual(self.client.post('/api/productos', json={}, headers=self.headers()).status_code, 403)
        self.db.table.assert_not_called()

    def test_token_expirado_y_claims_invalidos(self):
        for claims in [{'exp': 1}, {'usuario_id': True}, {'usuario_id': '1'}, {'roles': ['OTRO']}]:
            with self.subTest(claims=claims):
                self.assertEqual(self.client.get('/api/auth/perfil', headers=self.headers(**claims)).status_code, 401)
        token = jwt.encode({'usuario_id': 1, 'roles': ['CLIENTE']}, self.secret, algorithm='HS256')
        self.assertEqual(self.client.get('/api/auth/perfil', headers={'Authorization': 'Bearer ' + token}).status_code, 401)

    def test_secreto_obligatorio(self):
        with patch.object(backend, 'JWT_SECRET_KEY', ''):
            self.assertEqual(self.client.get('/api/auth/perfil', headers=self.headers()).status_code, 503)
            with self.assertRaises(RuntimeError):
                backend.clave_jwt()

    def test_json_y_textos_invalidos(self):
        for ruta in ['/api/auth/login', '/api/auth/registro', '/api/pedidos']:
            for data in [[], 'texto', 12, {'email': None}, {'email': 23}]:
                with self.subTest(ruta=ruta, data=data):
                    self.assertEqual(self.client.post(ruta, json=data, headers=self.headers()).status_code, 400)
        self.assertEqual(self.client.post('/api/auth/login', data='{', content_type='application/json').status_code, 400)
        self.db.table.assert_not_called()
        self.db.rpc.assert_not_called()

    def test_cantidades_e_ids_invalidos(self):
        for campo in ['cantidad', 'producto_id']:
            for valor in [None, True, False, 0, -1, 1.5, '2', {}, 2147483648]:
                item = {'producto_id': 2, 'cantidad': 1, campo: valor}
                with self.subTest(campo=campo, valor=valor):
                    self.assertEqual(self.pedido(items=[item]).status_code, 400)
        for items in [[], {}, 'texto', [None], [2]]:
            self.assertEqual(self.pedido(items=items).status_code, 400)
        self.db.rpc.assert_not_called()

    def test_precios_invalidos(self):
        for precio in [None, True, [], {}, -1, 'NaN', 'Infinity', 'pizza', '1.001', 100000000]:
            with self.subTest(precio=precio):
                respuesta = self.client.post('/api/productos', json={'nombre': 'Pizza', 'precio': precio}, headers=self.headers('ADMINISTRADOR'))
                self.assertEqual(respuesta.status_code, 400)
        self.db.rpc.assert_not_called()

    def test_stock_inicial_invalido(self):
        for stock in [-1, True, '10', 2.5, None]:
            self.assertEqual(self.client.post('/api/productos', json={'nombre': 'Pizza', 'precio': 10, 'stock_inicial': stock}, headers=self.headers('ADMINISTRADOR')).status_code, 400)
        self.db.rpc.assert_not_called()

    def test_booleano_real_al_actualizar(self):
        for valor in ['false', 0, None]:
            self.assertEqual(self.client.put('/api/productos/2', json={'activo': valor}, headers=self.headers('ADMINISTRADOR')).status_code, 400)
        self.db.table.assert_not_called()

    def test_pedido_usa_identidad_del_token_y_no_precio_del_cliente(self):
        resultado = {'pedido': {'id': 5, 'total': 20}, 'detalles': []}
        self.db.rpc.return_value.execute.return_value = SimpleNamespace(data=resultado)
        respuesta = self.pedido(usuario_id=999, total=0, items=[{'producto_id': 2, 'cantidad': 2, 'precio': 0}])
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json['data'], resultado)
        nombre, argumentos = self.db.rpc.call_args.args
        self.assertEqual(nombre, 'crear_pedido_atomico')
        self.assertEqual(argumentos['p_usuario_id'], 1)
        self.assertEqual(argumentos['p_items'], [{'producto_id': 2, 'cantidad': 2}])
        self.db.table.assert_not_called()

    def test_producto_e_inventario_se_crean_por_rpc(self):
        self.db.rpc.return_value.execute.return_value = SimpleNamespace(data={'id': 2, 'nombre': 'Pizza'})
        respuesta = self.client.post('/api/productos', json={'nombre': 'Pizza', 'precio': '10.50', 'stock_inicial': 0}, headers=self.headers('ADMINISTRADOR'))
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(self.db.rpc.call_args.args[0], 'crear_producto_con_inventario')
        self.assertEqual(self.db.rpc.call_args.args[1]['p_stock_inicial'], 0)
        self.db.table.assert_not_called()

    def test_producto_inactivo_o_sin_stock_devuelve_400(self):
        for mensaje in ['El producto 2 no está disponible.', 'Stock insuficiente para el producto 2.']:
            self.db.rpc.return_value.execute.side_effect = APIError({'code': 'P0001', 'message': mensaje, 'details': None, 'hint': None})
            respuesta = self.pedido()
            self.assertEqual(respuesta.status_code, 400)
            self.assertEqual(respuesta.json['mensaje'], mensaje)

    def test_error_interno_no_se_expone(self):
        self.db.rpc.return_value.execute.side_effect = RuntimeError('credencial-interna-no-publica')
        respuesta = self.pedido()
        self.assertEqual(respuesta.status_code, 500)
        self.assertNotIn('credencial-interna', respuesta.get_data(as_text=True))

    def test_registro_no_permite_escalar_roles(self):
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])
        self.db.table.return_value.insert.return_value.execute.return_value = SimpleNamespace(data=[{
            'id': 1, 'nombre': 'Cliente', 'email': 'cliente@example.test', 'roles': ['CLIENTE']}])
        respuesta = self.client.post('/api/auth/registro', json={
            'nombre': 'Cliente', 'email': 'cliente@example.test', 'password': 'Prueba123!',
            'roles': ['ADMINISTRADOR'], 'rol': 'ADMINISTRADOR'})
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json['data']['roles'], ['CLIENTE'])
        self.assertNotIn('password_hash', respuesta.json['data'])
        self.assertEqual(self.db.table.return_value.insert.call_args.args[0]['roles'], ['CLIENTE'])

    def test_password_no_se_recorta(self):
        with backend.app.test_request_context(json={'password': '  secreto  '}):
            self.assertEqual(backend.texto(backend.datos_json(), 'password', recortar=False), '  secreto  ')

    def test_password_solo_espacios_no_se_acepta(self):
        for ruta in ['/api/auth/login', '/api/auth/registro']:
            respuesta = self.client.post(ruta, json={'nombre': 'Cliente', 'email': 'cliente@example.test', 'password': '      '})
            self.assertEqual(respuesta.status_code, 400)
        self.db.table.assert_not_called()

    def test_catalogo_y_detalle_filtran_productos_activos(self):
        consulta = self.db.table.return_value
        consulta.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = SimpleNamespace(data=[])
        self.assertEqual(self.client.get('/api/productos').status_code, 200)
        consulta.select.return_value.eq.assert_called_with('activo', True)
        consulta.select.return_value.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])
        self.assertEqual(self.client.get('/api/productos/2').status_code, 404)
        consulta.select.return_value.eq.return_value.eq.assert_called_with('activo', True)


if __name__ == '__main__':
    unittest.main()
