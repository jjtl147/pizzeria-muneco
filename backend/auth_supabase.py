"""Supabase Auth por HTTP. Las claves de servicio permanecen en Flask.

Cada petición lleva su propia autorización: una sesión de usuario nunca cambia
el cliente privilegiado que se utiliza para las operaciones de datos.
"""
import os
import time
from urllib.parse import urlencode

import httpx
from werkzeug.security import check_password_hash


class AuthFailure(Exception):
    def __init__(self, status=401, code='invalid_credentials'):
        self.status = status
        self.code = code
        super().__init__('Supabase Auth rechazó la solicitud.')


def solicitar(method, path, datos=None, token=None):
    url = os.getenv('SUPABASE_URL', '').strip().split('/rest/v1')[0].rstrip('/')
    key = os.getenv('SUPABASE_KEY', '').strip()
    if not url or not key or 'tu-proyecto' in url:
        raise RuntimeError('Configure Supabase en backend/.env.')
    headers = {'apikey': key}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    elif path.startswith('/admin/'):
        headers['Authorization'] = f'Bearer {key}'
    response = httpx.request(method, f'{url}/auth/v1{path}', headers=headers,
                            json=datos, timeout=15)
    if response.is_error:
        try:
            code = response.json().get('error_code') or response.json().get('code')
        except ValueError:
            code = None
        raise AuthFailure(response.status_code, code)
    return response.json() if response.content else {}


def redireccion(ruta):
    base = os.getenv('FRONTEND_URL', 'http://127.0.0.1:5173').rstrip('/')
    return urlencode({'redirect_to': base + ruta})


def sesion_publica(datos):
    return {'token': datos['access_token'], 'refresh_token': datos['refresh_token'],
            'expires_at': int(time.time()) + int(datos.get('expires_in', 3600))}


def iniciar_sesion(db, email, password):
    # Leer la nueva columna antes de crear nada en Auth. Si falta 003, no migrar.
    existentes = db.table('usuarios').select(
        'id,email,auth_user_id,password_hash').eq('email', email).execute().data
    try:
        return solicitar('POST', '/token?grant_type=password', {'email': email, 'password': password})
    except AuthFailure as error:
        if error.code != 'invalid_credentials' or not existentes:
            raise
        anterior = existentes[0]
        if anterior.get('auth_user_id') or not anterior.get('password_hash'):
            raise
        if not check_password_hash(anterior['password_hash'], password):
            raise
        # Importación de una identidad ya autenticada en el sistema anterior.
        # Solo app_metadata, escrita por el servidor, puede reclamar su perfil.
        # El trigger conserva ID/roles y elimina el hash heredado atómicamente.
        solicitar('POST', '/admin/users', {
            'email': email, 'password': password, 'email_confirm': True,
            'app_metadata': {'legacy_usuario_id': anterior['id']},
        })
        return solicitar('POST', '/token?grant_type=password', {'email': email, 'password': password})
