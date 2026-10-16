import io
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
from werkzeug.security import generate_password_hash

import app
import auth_supabase as auth


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        self.db = MagicMock()
        self.profile = {'id': 8, 'nombre': 'Cliente', 'roles': ['CLIENTE']}
        self.session = {'access_token': 'access', 'refresh_token': 'refresh',
                        'expires_in': 3600, 'user': {'id': 'uuid-auth'}}
        for item in [patch.object(app, 'get_supabase_client', return_value=self.db),
                     patch.object(app, 'cargar_usuario', return_value=self.profile)]:
            item.start(); self.addCleanup(item.stop)

    def test_identidad_se_valida_en_auth_sin_confiar_en_jwt_local(self):
        with patch.object(app, 'solicitar', side_effect=auth.AuthFailure(401)) as remoto:
            r = self.client.get('/api/usuarios', headers={'Authorization': 'Bearer jwt-local-antiguo'})
        self.assertEqual(r.status_code, 401)
        remoto.assert_called_once_with('GET', '/user', token='jwt-local-antiguo')

    def test_auth_no_disponible_no_cierra_sesion_como_credenciales_invalidas(self):
        with patch.object(app, 'solicitar', side_effect=httpx.ConnectError('privado')):
            r = self.client.get('/api/auth/perfil', headers={'Authorization': 'Bearer access'})
        self.assertEqual(r.status_code, 503)
        self.assertNotIn('privado', r.get_data(as_text=True))

    def test_registro_ignora_roles_y_app_metadata_del_cliente(self):
        with patch.object(app, 'solicitar', return_value={'id': 'uuid'}) as remoto:
            r = self.client.post('/api/auth/registro', json={
                'nombre': 'Prueba', 'email': 'prueba@example.test', 'password': 'Prueba123!',
                'roles': ['ADMINISTRADOR'], 'app_metadata': {'legacy_usuario_id': 1}})
        self.assertEqual(r.status_code, 202)
        datos = remoto.call_args.args[2]
        self.assertEqual(set(datos['data']), {'nombre', 'telefono', 'direccion'})
        self.assertNotIn('app_metadata', datos)
        self.db.table.return_value.insert.assert_not_called()

    def test_registro_no_crea_identidad_si_falta_migracion(self):
        self.db.table.return_value.select.return_value.limit.return_value.execute.side_effect = RuntimeError('falta columna')
        with patch.object(app, 'solicitar') as remoto:
            r = self.client.post('/api/auth/registro', json={
                'nombre': 'Prueba', 'email': 'prueba@example.test', 'password': 'Prueba123!'})
        self.assertEqual(r.status_code, 503)
        remoto.assert_not_called()

    def test_login_y_renovacion_devuelven_sesion_supabase_y_perfil_vigente(self):
        with patch.object(app, 'iniciar_sesion', return_value=self.session):
            r = self.client.post('/api/auth/login', json={'email': 'p@example.test', 'password': '  secreto  '})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['token'], 'access')
        self.assertEqual(r.json['usuario']['id'], 8)
        self.assertEqual(r.headers['Cache-Control'], 'no-store')
        with patch.object(app, 'solicitar', return_value=self.session) as remoto:
            r = self.client.post('/api/auth/renovar', json={'refresh_token': 'refresh'})
        self.assertEqual(r.status_code, 200)
        remoto.assert_called_once_with('POST', '/token?grant_type=refresh_token', {'refresh_token': 'refresh'})

    def test_migracion_exige_password_anterior_y_conserva_id(self):
        legacy = {'id': 8, 'email': 'p@example.test', 'auth_user_id': None,
                  'password_hash': generate_password_hash('Anterior123!')}
        self.db.table.return_value.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[legacy])
        with patch.object(auth, 'solicitar', side_effect=[auth.AuthFailure(400, 'invalid_credentials'), {}, self.session]) as remoto:
            self.assertEqual(auth.iniciar_sesion(self.db, legacy['email'], 'Anterior123!'), self.session)
        self.assertEqual(remoto.call_args_list[1].args[2]['app_metadata'], {'legacy_usuario_id': 8})
        for cambios, password in [({}, 'Incorrecta'), ({'auth_user_id': 'ya-vinculado'}, 'Anterior123!'),
                                   ({'password_hash': None}, 'Anterior123!')]:
            self.db.table.return_value.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[{**legacy, **cambios}])
            with patch.object(auth, 'solicitar', side_effect=auth.AuthFailure(400, 'invalid_credentials')) as remoto:
                with self.assertRaises(auth.AuthFailure): auth.iniciar_sesion(self.db, legacy['email'], password)
                self.assertEqual(remoto.call_count, 1)

    def test_correo_sin_confirmar_no_inicia_migracion(self):
        with patch.object(auth, 'solicitar', side_effect=auth.AuthFailure(400, 'email_not_confirmed')) as remoto:
            with self.assertRaises(auth.AuthFailure): auth.iniciar_sesion(self.db, 'p@example.test', 'Prueba123!')
            self.assertEqual(remoto.call_count, 1)

    def test_recuperacion_no_enumera_cuentas(self):
        respuestas = []
        for efecto in [None, auth.AuthFailure(404, 'user_not_found')]:
            with patch.object(app, 'solicitar', return_value={}, side_effect=efecto):
                respuestas.append(self.client.post('/api/auth/recuperar', json={'email': 'p@example.test'}))
        self.assertEqual(respuestas[0].json, respuestas[1].json)
        self.assertEqual(respuestas[0].status_code, 200)

    def test_password_exige_token_y_revoca_refresh_tokens(self):
        self.assertEqual(self.client.put('/api/auth/password', json={'password': 'Nueva123!'}).status_code, 401)
        with patch.object(app, 'identidad_supabase', return_value='uuid'), patch.object(app, 'solicitar', return_value={}) as remoto:
            r = self.client.put('/api/auth/password', json={'password': 'Nueva123!'}, headers={'Authorization': 'Bearer recovery'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(remoto.call_args_list[0].args, ('PUT', '/user', {'password': 'Nueva123!'}))
        self.assertEqual(remoto.call_args_list[1].args, ('POST', '/logout?scope=global'))

    def test_peticion_auth_no_contamina_cliente_de_datos_ni_expone_errores(self):
        with patch.dict(os.environ, {'SUPABASE_URL': 'https://example.test', 'SUPABASE_KEY': 'solo-servidor'}):
            with patch.object(auth.httpx, 'request', return_value=httpx.Response(200, json={'id': 'uuid'})) as remoto:
                auth.solicitar('GET', '/user', token='token-usuario')
                headers = remoto.call_args.kwargs['headers']
                self.assertEqual(headers, {'apikey': 'solo-servidor', 'Authorization': 'Bearer token-usuario'})
            with patch.object(auth.httpx, 'request', return_value=httpx.Response(400, json={'error_code': 'invalid_credentials', 'msg': 'privado'})):
                with self.assertRaises(auth.AuthFailure) as ctx: auth.solicitar('POST', '/token')
                self.assertNotIn('privado', str(ctx.exception))

    def test_storage_rechaza_rol_cliente_archivos_y_tamanos_invalidos(self):
        with patch.object(app, 'identidad_supabase', return_value='uuid'):
            r = self.client.post('/api/productos/imagen', headers={'Authorization': 'Bearer access'})
            self.assertEqual(r.status_code, 403)
            self.profile['roles'] = ['ADMINISTRADOR']
            for contenido, esperado in [(b'<svg></svg>', 400), (b'x' * (5 * 1024 * 1024 + 1), 413)]:
                r = self.client.post('/api/productos/imagen', data={'imagen': (io.BytesIO(contenido), 'foto.png')}, headers={'Authorization': 'Bearer access'})
                self.assertEqual(r.status_code, esperado)
                r.request.input_stream.close()
            self.db.storage.from_.assert_not_called()

    def test_storage_usa_nombre_aleatorio_y_mime_detectado(self):
        self.profile['roles'] = ['ADMINISTRADOR']
        bucket = self.db.storage.from_.return_value
        bucket.get_public_url.return_value = 'https://example.test/storage/foto.png'
        with patch.object(app, 'identidad_supabase', return_value='uuid'):
            r = self.client.post('/api/productos/imagen', data={'imagen': (io.BytesIO(b'\x89PNG\r\n\x1a\ncontenido'), '../../foto.html')}, headers={'Authorization': 'Bearer access'})
        self.assertEqual(r.status_code, 201)
        ruta, _, opciones = bucket.upload.call_args.args
        self.assertRegex(ruta, r'^[a-f0-9]{32}\.png$')
        self.assertEqual(opciones['content-type'], 'image/png')


if __name__ == '__main__':
    unittest.main()
