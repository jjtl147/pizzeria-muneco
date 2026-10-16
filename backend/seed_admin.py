"""Crear el administrador inicial con Supabase Auth, solo desde consola local."""
import getpass
from app import get_supabase_client, cargar_usuario
from auth_supabase import iniciar_sesion, solicitar


def main():
    db = get_supabase_client()
    # Comprobar 003 antes de crear identidades o pedir credenciales.
    db.table('usuarios').select('auth_user_id').limit(0).execute()
    administradores = db.table('usuarios').select('id').contains('roles', ['ADMINISTRADOR']).limit(1).execute()
    if administradores.data:
        raise SystemExit('Ya existe un administrador. Asigne otros roles desde el panel de usuarios.')
    nombre = input('Nombre del administrador: ').strip()
    email = input('Correo: ').strip().lower()
    if not nombre or len(nombre) > 100 or email.count('@') != 1 or len(email) > 150 or any(c.isspace() for c in email):
        raise SystemExit('Nombre o correo inválidos.')
    existente = db.table('usuarios').select('id,roles').eq('email', email).execute().data
    if existente:
        password = getpass.getpass('Contraseña actual de esa cuenta: ')
        sesion = iniciar_sesion(db, email, password)
        usuario = cargar_usuario(sesion['user']['id'])
        if not usuario or usuario['id'] != existente[0]['id']:
            raise SystemExit('La identidad no coincide con el perfil.')
        solicitar('POST', '/logout?scope=local', token=sesion['access_token'])
    else:
        password = getpass.getpass('Contraseña nueva (al menos 8 caracteres): ')
        if len(password) < 8 or not password.strip():
            raise SystemExit('Contraseña inválida.')
        if password != getpass.getpass('Repita la contraseña: '):
            raise SystemExit('Las contraseñas no coinciden.')
        # Bootstrap local autorizado: no requiere enviar correos.
        identidad = solicitar('POST', '/admin/users', {
            'email': email, 'password': password, 'email_confirm': True,
            'user_metadata': {'nombre': nombre},
        })
        usuario = cargar_usuario(identidad['id'])
        if not usuario:
            raise SystemExit('No se creó el perfil. Revise la migración 003.')
    roles = sorted(set(usuario['roles']) | {'CLIENTE', 'ADMINISTRADOR'})
    db.table('usuarios').update({'roles': roles}).eq('id', usuario['id']).execute()
    print('Administrador inicial configurado en Supabase Auth. Inicie sesión desde la aplicación.')


if __name__ == '__main__':
    main()
