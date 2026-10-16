import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app


class FiltrosTests(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        self.usuario = {'id': 7, 'nombre': 'Prueba', 'roles': ['ADMINISTRADOR']}
        self.db = MagicMock()
        self.consulta = MagicMock()
        for metodo in ('select', 'order', 'eq', 'gte', 'lt', 'ilike', 'range'):
            getattr(self.consulta, metodo).return_value = self.consulta
        self.consulta.execute.return_value = SimpleNamespace(data=[])
        self.db.table.return_value = self.consulta
        self.db.rpc.return_value.execute.return_value = SimpleNamespace(data={})
        for item in (patch.object(app, 'identidad_supabase', return_value='uuid'),
                     patch.object(app, 'cargar_usuario', side_effect=lambda _: self.usuario),
                     patch.object(app, 'get_supabase_client', return_value=self.db)):
            item.start(); self.addCleanup(item.stop)
        self.headers = {'Authorization': 'Bearer access'}

    def test_email_se_filtra_en_servidor_y_se_pagina_despues(self):
        r = self.client.get('/api/usuarios?email=%20VENDEDOR%40EXAMPLE.TEST%20&pagina=2', headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.consulta.ilike.assert_called_once_with('email', '%vendedor@example.test%')
        self.consulta.range.assert_called_once_with(50, 99)

    def test_email_guion_bajo_literal_y_rechazo_de_comodines(self):
        r = self.client.get('/api/usuarios?email=nombre_apellido', headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.consulta.ilike.assert_called_once_with('email', '%nombre\\_apellido%')
        self.db.reset_mock()
        for email in ['%', '*', 'a b', '\\', 'a' * 151]:
            with self.subTest(email=email):
                r = self.client.get('/api/usuarios', query_string={'email': email}, headers=self.headers)
                self.assertEqual(r.status_code, 400)
        self.db.table.assert_not_called()

    def test_ventas_y_reportes_requieren_ambas_fechas_sin_consultar_datos(self):
        for ruta in ('/api/ventas', '/api/reportes/ventas'):
            for params in ({}, {'desde': '2026-10-01'}, {'hasta': '2026-10-07'},
                           {'desde': '2026-10-07', 'hasta': '2026-10-01'},
                           {'desde': 'invalida', 'hasta': '2026-10-07'},
                           {'desde': '2025-01-01', 'hasta': '2026-10-07'}):
                with self.subTest(ruta=ruta, params=params):
                    r = self.client.get(ruta, query_string=params, headers=self.headers)
                    self.assertEqual(r.status_code, 400)
        self.db.table.assert_not_called()
        self.db.rpc.assert_not_called()

    def test_ventas_filtran_dia_completo_en_bolivia_y_conservan_propiedad(self):
        self.usuario['roles'] = ['VENDEDOR']
        r = self.client.get('/api/ventas?desde=2026-10-01&hasta=2026-10-01', headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.consulta.gte.assert_called_once_with('fecha_venta', '2026-10-01T00:00:00-04:00')
        self.consulta.lt.assert_called_once_with('fecha_venta', '2026-10-02T00:00:00-04:00')
        self.consulta.eq.assert_called_once_with('vendedor_id', 7)
        self.consulta.range.assert_called_once_with(0, 49)

    def test_admin_consulta_todas_las_ventas_del_periodo(self):
        r = self.client.get('/api/ventas?desde=2026-10-01&hasta=2026-10-07', headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.consulta.eq.assert_not_called()

    def test_reporte_explicito_y_vendedor_sin_acceso_administrativo(self):
        ruta = '/api/reportes/ventas?desde=2026-10-01&hasta=2026-10-07'
        r = self.client.get(ruta, headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.db.rpc.assert_called_once_with('reporte_ventas', {
            'p_desde': '2026-10-01T00:00:00-04:00', 'p_hasta': '2026-10-08T00:00:00-04:00'})
        self.usuario['roles'] = ['VENDEDOR']
        for endpoint in ('/api/usuarios?email=admin', ruta, '/api/inventario'):
            self.assertEqual(self.client.get(endpoint, headers=self.headers).status_code, 403)


if __name__ == '__main__':
    unittest.main()
