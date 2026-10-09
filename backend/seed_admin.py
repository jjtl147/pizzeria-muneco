"""Crear el administrador inicial: ejecutar localmente, nunca desde una ruta web."""
import getpass
from app import get_supabase_client
from werkzeug.security import generate_password_hash


def main():
    db = get_supabase_client()
    administradores = db.table('usuarios').select('id').contains('roles', ['ADMINISTRADOR']).limit(1).execute()
    if administradores.data:
        raise SystemExit('Ya existe un administrador. Asigne otros roles desde el panel de usuarios.')
    nombre = input('Nombre del administrador: ').strip()
    email = input('Correo: ').strip().lower()
    if not nombre or len(nombre) > 100 or email.count('@') != 1 or len(email) > 150:
        raise SystemExit('Nombre o correo inválidos.')
    existente = db.table('usuarios').select('id,roles').eq('email', email).execute().data
    if existente:
        password = getpass.getpass('Contraseña actual de esa cuenta: ')
        from werkzeug.security import check_password_hash
        usuario = db.table('usuarios').select('password_hash').eq('id', existente[0]['id']).execute().data[0]
        if not check_password_hash(usuario['password_hash'], password):
            raise SystemExit('Contraseña incorrecta.')
        roles = sorted(set(existente[0]['roles']) | {'ADMINISTRADOR'})
        db.table('usuarios').update({'roles': roles}).eq('id', existente[0]['id']).execute()
    else:
        password = getpass.getpass('Contraseña nueva (al menos 8 caracteres): ')
        if len(password) < 8 or not password.strip():
            raise SystemExit('Contraseña inválida.')
        if password != getpass.getpass('Repita la contraseña: '):
            raise SystemExit('Las contraseñas no coinciden.')
        db.table('usuarios').insert({'nombre': nombre, 'email': email,
            'password_hash': generate_password_hash(password), 'roles': ['CLIENTE', 'ADMINISTRADOR']}).execute()
    print('Administrador inicial configurado. Inicie sesión desde la aplicación.')


if __name__ == '__main__':
    main()
