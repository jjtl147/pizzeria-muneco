import os
import datetime
import uuid
from functools import wraps
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
from integrations import notificar_pedido, notificar_stock, responder_asistente
from postgrest.exceptions import APIError
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv
import httpx
from auth_supabase import AuthFailure, solicitar, redireccion, sesion_publica, iniciar_sesion
from supabase import create_client, Client, ClientOptions

load_dotenv()

app = Flask(__name__)
CORS(app)


@app.after_request
def no_cache_auth(response):
    if request.path.startswith('/api/auth/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.errorhandler(RequestEntityTooLarge)
def archivo_demasiado_grande(_error):
    return jsonify({'status': 'error', 'mensaje': 'La imagen admite como máximo 5 MB.'}), 413

def get_supabase_client() -> Client:
    url = os.getenv('SUPABASE_URL', '').strip()
    key = os.getenv('SUPABASE_KEY', '').strip()

    if not url or not key or 'tu-proyecto' in url:
        raise RuntimeError("Las credenciales de Supabase no están configuradas correctamente en el archivo .env")

    if '/rest/v1' in url:
        url = url.split('/rest/v1')[0]
    url = url.rstrip('/')

    return create_client(url, key, options=ClientOptions(
        auto_refresh_token=False, persist_session=False,
    ))

# Validaciones compartidas: los datos del navegador no son confiables.
def datos_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON válido.")
    return data


def texto(data, campo, obligatorio=False, limite=None, recortar=True):
    valor = data.get(campo, '')
    if not isinstance(valor, str):
        raise ValueError(f"El campo '{campo}' debe ser texto.")
    valor = valor.strip() if recortar else valor
    if obligatorio and not valor:
        raise ValueError(f"El campo '{campo}' es obligatorio.")
    if limite and len(valor) > limite:
        raise ValueError(f"El campo '{campo}' admite hasta {limite} caracteres.")
    return valor


def entero(valor, campo, minimo=1):
    if type(valor) is not int or not minimo <= valor <= 2147483647:
        raise ValueError(f"El campo '{campo}' debe ser un entero entre {minimo} y 2147483647.")
    return valor


def precio_validado(valor):
    if isinstance(valor, bool) or not isinstance(valor, (int, float, str)):
        raise ValueError("El precio debe ser un número válido mayor o igual a 0.")
    try:
        precio = Decimal(str(valor))
        if not precio.is_finite() or not 0 <= precio <= Decimal('99999999.99'):
            raise InvalidOperation()
        if precio != precio.quantize(Decimal('0.01')):
            raise InvalidOperation()
        return float(precio)
    except InvalidOperation:
        raise ValueError("El precio debe ser no negativo y tener como máximo dos decimales.") from None


# Supabase Auth valida la identidad; los permisos siempre se leen de usuarios.
def identidad_supabase(token):
    identidad = solicitar('GET', '/user', token=token)
    if not identidad.get('id'):
        raise AuthFailure()
    return identidad['id']


def token_requerido(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        partes = request.headers.get('Authorization', '').split()
        if len(partes) != 2 or partes[0] != 'Bearer':
            return jsonify({'status': 'error', 'mensaje': 'Inicie sesión para continuar.'}), 401
        try:
            auth_id = identidad_supabase(partes[1])
            usuario = cargar_usuario(auth_id)
            if not usuario:
                return jsonify({'status': 'error', 'mensaje': 'La cuenta no tiene un perfil habilitado.'}), 401
            validar_roles(usuario.get('roles'))
        except AuthFailure as error:
            status = 401 if error.status in (400, 401, 403, 404, 422) else 503
            return jsonify({'status': 'error', 'mensaje': 'La sesión no es válida. Inicie sesión nuevamente.'
                            if status == 401 else 'No se pudo verificar la sesión. Intente nuevamente.'}), status
        except Exception:
            # No registrar excepciones que puedan contener tokens o credenciales.
            app.logger.error('No se pudo verificar la sesión en Supabase.')
            return jsonify({'status': 'error', 'mensaje': 'No se pudo verificar la sesión. Revise la configuración y la migración 003.'}), 503
        return f({**usuario, 'usuario_id': usuario['id']}, *args, **kwargs)
    return decorador

ROLES = {'CLIENTE', 'VENDEDOR', 'ADMINISTRADOR'}
METODOS_PAGO = {'EFECTIVO', 'QR', 'TARJETA'}


def validar_roles(roles):
    if not isinstance(roles, list) or not roles or any(not isinstance(r, str) or r not in ROLES for r in roles):
        raise ValueError('Seleccione al menos un rol válido.')
    if len(roles) != len(set(roles)):
        raise ValueError('Los roles no deben repetirse.')
    return roles


def cargar_usuario(auth_user_id):
    resultado = get_supabase_client().table('usuarios').select(
        'id,nombre,email,roles,telefono,direccion,creado_en').eq('auth_user_id', auth_user_id).execute()
    return resultado.data[0] if resultado.data else None


def rol_requerido(*roles_permitidos):
    # OR entre permisos: basta tener uno de los roles solicitados.
    def envolver(f):
        @wraps(f)
        def decorador(usuario_actual, *args, **kwargs):
            if not set(usuario_actual.get('roles', [])) & set(roles_permitidos):
                return jsonify({'status': 'error', 'mensaje': 'No tiene permisos para esta operación.'}), 403
            return f(usuario_actual, *args, **kwargs)
        return decorador
    return envolver


def errores_api(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as error:
            return jsonify({'status': 'error', 'mensaje': str(error)}), 400
        except RequestEntityTooLarge:
            raise
        except APIError as error:
            if error.code == 'P0001':
                return jsonify({'status': 'error', 'mensaje': error.message}), 400
            if error.code == '23505':
                return jsonify({'status': 'error', 'mensaje': 'El registro ya existe.'}), 409
            if error.code in ('23503', '23514', '22003'):
                return jsonify({'status': 'error', 'mensaje': 'Los datos no cumplen las restricciones de la base.'}), 400
            app.logger.exception('Error de base de datos')
            return jsonify({'status': 'error', 'mensaje': 'No se pudo completar la operación.'}), 500
        except Exception:
            app.logger.exception('Error interno de API')
            return jsonify({'status': 'error', 'mensaje': 'No se pudo completar la operación.'}), 500
    return decorador


def items_validados(items):
    if not isinstance(items, list) or not items or len(items) > 100:
        raise ValueError('Incluya entre 1 y 100 productos.')
    resultado = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Cada ítem debe ser un objeto JSON.')
        resultado.append({'producto_id': entero(item.get('producto_id'), 'producto_id'),
                          'cantidad': entero(item.get('cantidad'), 'cantidad')})
    return resultado


def metodo_validado(data):
    metodo = texto(data, 'metodo_pago', obligatorio=True).upper()
    if metodo not in METODOS_PAGO:
        raise ValueError('Seleccione EFECTIVO, QR o TARJETA.')
    return metodo


def pagina_consulta(consulta):
    try:
        pagina = int(request.args.get('pagina', '1'))
    except ValueError:
        raise ValueError('Página inválida.') from None
    if pagina < 1:
        raise ValueError('Página inválida.')
    resultado = consulta.range((pagina - 1) * 50, pagina * 50 - 1).execute()
    data = resultado.data or []
    return jsonify({'status': 'success', 'data': data, 'pagina': pagina,
                    'hay_mas': len(data) == 50})


# ==========================================
# RUTAS DE ESTADO Y DOCUMENTACIÓN
# ==========================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "success",
        "mensaje": "API Pizzería Muñeco - Backend Flask activo",
        "endpoints_disponibles": [
            {"metodo": metodo, "ruta": regla.rule}
            for regla in app.url_map.iter_rules() if regla.endpoint != 'static'
            for metodo in sorted(regla.methods - {'HEAD', 'OPTIONS'})
        ]
    }), 200

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "status": "success",
        "mensaje": "Backend de Flask funcionando correctamente"
    }), 200

# ==========================================
# MÓDULO DE AUTENTICACIÓN (AUTH)
# ==========================================

def error_auth(error):
    if isinstance(error, ValueError):
        return jsonify({'status': 'error', 'mensaje': str(error)}), 400
    if isinstance(error, AuthFailure):
        if error.status == 429:
            return jsonify({'status': 'error', 'mensaje': 'Demasiados intentos. Espere unos minutos.'}), 429
        if error.code == 'email_not_confirmed':
            return jsonify({'status': 'error', 'mensaje': 'Confirme su correo antes de iniciar sesión.'}), 401
        if error.code == 'weak_password':
            return jsonify({'status': 'error', 'mensaje': 'La contraseña no cumple los requisitos configurados.'}), 400
        if error.status < 500:
            return jsonify({'status': 'error', 'mensaje': 'No se pudo autenticar. Revise sus datos o recupere el acceso.'}), 401
    app.logger.error('No se pudo completar una operación de Supabase Auth.')
    return jsonify({'status': 'error', 'mensaje': 'Autenticación no disponible. Revise Supabase y la migración 003.'}), 503


def correo_validado(data):
    email = texto(data, 'email', obligatorio=True, limite=150).lower()
    if email.count('@') != 1 or any(c.isspace() for c in email) or not all(email.split('@')):
        raise ValueError('El correo electrónico no es válido.')
    return email


def password_validado(data, nuevo=False):
    password = texto(data, 'password', obligatorio=True, limite=256, recortar=False)
    if not password.strip() or (nuevo and len(password) < 8):
        raise ValueError('La contraseña nueva debe tener al menos 8 caracteres y no puede estar vacía.')
    return password


def respuesta_sesion(datos):
    usuario = cargar_usuario(datos['user']['id'])
    if not usuario:
        raise RuntimeError('Falta el perfil de la identidad autenticada.')
    validar_roles(usuario.get('roles'))
    return jsonify({'status': 'success', **sesion_publica(datos), 'usuario': usuario})


@app.post('/api/auth/registro')
def registro():
    try:
        data = datos_json()
        nombre = texto(data, 'nombre', obligatorio=True, limite=100)
        email = correo_validado(data)
        password = password_validado(data, nuevo=True)
        telefono = texto(data, 'telefono', limite=20)
        direccion = texto(data, 'direccion', limite=1000)
        # Comprobar la migración antes de solicitar correo o crear una identidad.
        db = get_supabase_client()
        db.table('usuarios').select('auth_user_id').limit(0).execute()
        datos = solicitar('POST', '/signup?' + redireccion('/auth/callback'), {
            'email': email, 'password': password,
            'data': {'nombre': nombre, 'telefono': telefono, 'direccion': direccion},
        })
        # Supabase puede ocultar si una cuenta ya existe. No devolver identidades
        # ni asegurar creación: el mensaje es el mismo en ambos casos.
        if datos.get('access_token'):
            solicitar('POST', '/logout?scope=local', token=datos['access_token'])
        return jsonify({'status': 'success', 'mensaje':
            'Solicitud recibida. Si corresponde, recibirá un correo de confirmación. Luego podrá iniciar sesión.'}), 202
    except Exception as error:
        return error_auth(error)


@app.post('/api/auth/login')
def login():
    try:
        data = datos_json()
        email = correo_validado(data)
        password = password_validado(data)
        datos = iniciar_sesion(get_supabase_client(), email, password)
        return respuesta_sesion(datos)
    except Exception as error:
        return error_auth(error)


@app.post('/api/auth/renovar')
def renovar_sesion():
    try:
        refresh = texto(datos_json(), 'refresh_token', obligatorio=True, limite=4096)
        datos = solicitar('POST', '/token?grant_type=refresh_token', {'refresh_token': refresh})
        return respuesta_sesion(datos)
    except Exception as error:
        return error_auth(error)


@app.post('/api/auth/recuperar')
def recuperar_acceso():
    try:
        email = correo_validado(datos_json())
        solicitar('POST', '/recover?' + redireccion('/restablecer'), {'email': email})
        return jsonify({'status': 'success', 'mensaje':
            'Si la cuenta permite recuperar el acceso, recibirá un enlace en su correo.'})
    except AuthFailure as error:
        if error.status in (400, 404, 422):
            return jsonify({'status': 'success', 'mensaje':
                'Si la cuenta permite recuperar el acceso, recibirá un enlace en su correo.'})
        return error_auth(error)
    except Exception as error:
        return error_auth(error)


@app.post('/api/auth/logout')
@token_requerido
def logout(_usuario):
    try:
        solicitar('POST', '/logout?scope=local', token=request.headers['Authorization'].split()[1])
        return jsonify({'status': 'success'})
    except Exception as error:
        return error_auth(error)


@app.put('/api/auth/password')
@token_requerido
def cambiar_password(_usuario):
    try:
        password = password_validado(datos_json(), nuevo=True)
        token = request.headers['Authorization'].split()[1]
        solicitar('PUT', '/user', {'password': password}, token=token)
        solicitar('POST', '/logout?scope=global', token=token)
        return jsonify({'status': 'success', 'mensaje': 'Contraseña actualizada. Inicie sesión nuevamente.'})
    except Exception as error:
        return error_auth(error)

@app.route('/api/auth/perfil', methods=['GET'])
@token_requerido
def perfil(usuario_actual):
    try:
        supabase = get_supabase_client()
        resultado = supabase.table('usuarios')\
            .select('id, nombre, email, roles, telefono, direccion, creado_en')\
            .eq('id', usuario_actual['usuario_id'])\
            .execute()

        if not resultado.data or len(resultado.data) == 0:
            return jsonify({
                "status": "error",
                "mensaje": "Usuario no encontrado."
            }), 404

        return jsonify({
            "status": "success",
            "usuario": resultado.data[0]
        }), 200

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/auth/perfil]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al obtener perfil. Consulte al administrador si el problema persiste."
        }), 500

# ==========================================
# MÓDULO CRUD DE PRODUCTOS
# ==========================================

@app.post('/api/productos/imagen')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def subir_imagen(_usuario):
    request.max_content_length = 6 * 1024 * 1024  # Incluye el contenedor multipart.
    archivo = request.files.get('imagen')
    if not archivo:
        raise ValueError('Seleccione una imagen JPEG, PNG o WebP.')
    contenido = archivo.read(5 * 1024 * 1024 + 1)
    if len(contenido) > 5 * 1024 * 1024:
        return jsonify({'status': 'error', 'mensaje': 'La imagen admite como máximo 5 MB.'}), 413
    if contenido.startswith(b'\x89PNG\r\n\x1a\n'):
        extension, mime = 'png', 'image/png'
    elif contenido.startswith(b'\xff\xd8\xff'):
        extension, mime = 'jpg', 'image/jpeg'
    elif contenido[:4] == b'RIFF' and contenido[8:12] == b'WEBP':
        extension, mime = 'webp', 'image/webp'
    else:
        raise ValueError('Formato no admitido. Use JPEG, PNG o WebP.')
    bucket = get_supabase_client().storage.from_('productos')
    ruta = f'{uuid.uuid4().hex}.{extension}'
    bucket.upload(ruta, contenido, {'content-type': mime, 'upsert': 'false'})
    return jsonify({'status': 'success', 'url': bucket.get_public_url(ruta)}), 201


@app.route('/api/productos', methods=['GET'])
def obtener_productos():
    try:
        supabase = get_supabase_client()
        response = supabase.table('productos').select('*,inventario(stock_actual)').eq('activo', True).order('id').limit(500).execute()

        productos = response.data or []

        return jsonify({
            "status": "success",
            "total": len(productos),
            "data": productos
        }), 200

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/productos GET]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al consultar productos. Consulte al administrador si el problema persiste."
        }), 500

@app.route('/api/productos/<int:producto_id>', methods=['GET'])
def obtener_producto_detalle(producto_id):
    try:
        supabase = get_supabase_client()
        response = supabase.table('productos').select('*').eq('id', producto_id).eq('activo', True).execute()

        if not response.data or len(response.data) == 0:
            return jsonify({
                "status": "error",
                "mensaje": "Producto no encontrado."
            }), 404

        return jsonify({
            "status": "success",
            "data": response.data[0]
        }), 200

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/productos/<id> GET]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al consultar el producto. Consulte al administrador si el problema persiste."
        }), 500

@app.route('/api/productos', methods=['POST'])
@token_requerido
@rol_requerido('ADMINISTRADOR')
def crear_producto(usuario_actual):
    try:
        data = datos_json()
        nombre = texto(data, 'nombre', limite=100)
        descripcion = texto(data, 'descripcion')
        precio = data.get('precio')
        categoria_id = data.get('categoria_id')
        imagen = texto(data, 'imagen')

        if not nombre or precio is None:
            return jsonify({
                "status": "error",
                "mensaje": "Los campos 'nombre' y 'precio' son obligatorios."
            }), 400

        precio_num = precio_validado(precio)
        if categoria_id is not None:
            entero(categoria_id, 'categoria_id')
        stock_inicial = entero(data.get('stock_inicial', 50), 'stock_inicial', minimo=0)

        supabase = get_supabase_client()

        nuevo_producto = {
            'nombre': nombre,
            'descripcion': descripcion if descripcion else None,
            'precio': precio_num,
            'categoria_id': categoria_id if categoria_id else None,
            'imagen': imagen if imagen else 'https://placehold.co/400x300?text=Pizza',
            'activo': True,
            'tamano': texto(data, 'tamano', limite=40) or None
        }

        # Producto e inventario se crean juntos; un fallo revierte ambos.
        resultado = supabase.rpc('crear_producto_con_inventario', {
            'p_producto': nuevo_producto,
            'p_stock_inicial': stock_inicial
        }).execute()
        producto_creado = resultado.data
        if not producto_creado:
            raise RuntimeError("No se pudo crear el producto.")

        return jsonify({
            "status": "success",
            "mensaje": "Producto creado exitosamente.",
            "data": producto_creado
        }), 201

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/productos POST]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al crear producto. Consulte al administrador si el problema persiste."
        }), 500

@app.route('/api/productos/<int:producto_id>', methods=['PUT'])
@token_requerido
@rol_requerido('ADMINISTRADOR')
def actualizar_producto(usuario_actual, producto_id):
    try:
        data = datos_json()
        campos_actualizar = {}
        for campo in ('nombre', 'descripcion', 'imagen', 'tamano'):
            if campo in data:
                campos_actualizar[campo] = texto(data, campo, obligatorio=campo == 'nombre',
                                                limite=100 if campo == 'nombre' else 40 if campo == 'tamano' else None)
        if 'precio' in data:
            campos_actualizar['precio'] = precio_validado(data['precio'])
        if 'categoria_id' in data:
            categoria_id = data['categoria_id']
            campos_actualizar['categoria_id'] = (entero(categoria_id, 'categoria_id')
                                                 if categoria_id is not None else None)
        if 'activo' in data:
            if type(data['activo']) is not bool:
                raise ValueError("El campo 'activo' debe ser booleano.")
            campos_actualizar['activo'] = data['activo']

        if not campos_actualizar:
            return jsonify({
                "status": "error",
                "mensaje": "No se enviaron campos válidos para actualizar."
            }), 400

        supabase = get_supabase_client()

        existente = supabase.table('productos').select('id').eq('id', producto_id).execute()
        if not existente.data or len(existente.data) == 0:
            return jsonify({
                "status": "error",
                "mensaje": "El producto no existe."
            }), 404

        resultado = supabase.table('productos').update(campos_actualizar).eq('id', producto_id).execute()

        return jsonify({
            "status": "success",
            "mensaje": "Producto actualizado correctamente.",
            "data": resultado.data[0] if resultado.data else {}
        }), 200

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/productos/<id> PUT]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al actualizar el producto. Consulte al administrador si el problema persiste."
        }), 500

@app.route('/api/productos/<int:producto_id>', methods=['DELETE'])
@token_requerido
@rol_requerido('ADMINISTRADOR')
def eliminar_producto(usuario_actual, producto_id):
    try:
        supabase = get_supabase_client()
        existente = supabase.table('productos').select('id').eq('id', producto_id).execute()
        if not existente.data or len(existente.data) == 0:
            return jsonify({
                "status": "error",
                "mensaje": "El producto no existe."
            }), 404

        resultado = supabase.table('productos').update({'activo': False}).eq('id', producto_id).execute()

        return jsonify({
            "status": "success",
            "mensaje": f"Producto ID {producto_id} desactivado del catálogo correctamente."
        }), 200

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/productos/<id> DELETE]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al eliminar producto. Consulte al administrador si el problema persiste."
        }), 500

# ==========================================
# MÓDULO DE PEDIDOS
# ==========================================

@app.route('/api/pedidos', methods=['POST'])
@token_requerido
@rol_requerido('CLIENTE')
def crear_pedido(usuario_actual):
    try:
        data = datos_json()
        direccion_entrega = texto(data, 'direccion_entrega', obligatorio=True)
        telefono_contacto = texto(data, 'telefono_contacto', limite=20)
        metodo_pago = metodo_validado(data) if 'metodo_pago' in data else 'EFECTIVO'
        items = items_validados(data.get('items'))

        # PostgreSQL valida disponibilidad, calcula precios y descuenta stock
        # en una sola transacción, incluso cuando llegan compras simultáneas.
        resultado = get_supabase_client().rpc('crear_pedido_atomico', {
            'p_usuario_id': usuario_actual['usuario_id'],
            'p_direccion_entrega': direccion_entrega,
            'p_telefono_contacto': telefono_contacto or None,
            'p_metodo_pago': metodo_pago,
            'p_items': items
        }).execute()
        if not resultado.data:
            raise RuntimeError("No se pudo registrar el pedido.")
        notificar_pedido(resultado.data['pedido'], get_supabase_client)
        return jsonify({
            "status": "success",
            "mensaje": "Pedido registrado exitosamente.",
            "data": resultado.data
        }), 201

    except APIError as e:
        if e.code == 'P0001':
            return jsonify({"status": "error", "mensaje": e.message}), 400
        app.logger.exception("Error de base de datos al crear pedido")
        return jsonify({"status": "error", "mensaje": "No se pudo registrar el pedido."}), 500
    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/pedidos POST]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al procesar el pedido. Consulte al administrador si el problema persiste."
        }), 500

@app.route('/api/pedidos/mis-pedidos', methods=['GET'])
@token_requerido
@rol_requerido('CLIENTE')
def mis_pedidos(usuario_actual):
    try:
        supabase = get_supabase_client()
        consulta = supabase.table('pedidos').select(
            'id,fecha_pedido,estado,total,direccion_entrega,metodo_pago,detalle_pedidos(*)'
        ).eq('usuario_id', usuario_actual['usuario_id']).order('id', desc=True)
        return pagina_consulta(consulta)

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/pedidos/mis-pedidos GET]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al consultar el historial de pedidos. Consulte al administrador si el problema persiste."
        }), 500

@app.route('/api/pedidos', methods=['GET'])
@token_requerido
@rol_requerido('ADMINISTRADOR', 'VENDEDOR')
def listar_todos_los_pedidos(usuario_actual):
    try:
        supabase = get_supabase_client()
        consulta = supabase.table('pedidos').select(
            '*,usuarios(nombre,email),detalle_pedidos(*),ventas(id,metodo_pago,total)'
        ).order('id', desc=True)
        return pagina_consulta(consulta)

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/pedidos GET]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al consultar pedidos globales. Consulte al administrador si el problema persiste."
        }), 500

# ==========================================
# OPERACIÓN: ADMINISTRADOR Y VENDEDOR
# ==========================================

@app.get('/api/admin/productos')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def productos_admin(usuario_actual):
    return pagina_consulta(get_supabase_client().table('productos').select('*').order('id'))


@app.get('/api/categorias')
@errores_api
def categorias_publicas():
    resultado = get_supabase_client().table('categorias').select('*').eq('activo', True).order('nombre').execute()
    return jsonify({'status': 'success', 'data': resultado.data or []})


@app.get('/api/admin/categorias')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def categorias_admin(usuario_actual):
    return pagina_consulta(get_supabase_client().table('categorias').select('*').order('id'))


@app.route('/api/categorias', methods=['POST'])
@app.route('/api/categorias/<int:categoria_id>', methods=['PUT', 'DELETE'])
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def guardar_categoria(usuario_actual, categoria_id=None):
    db = get_supabase_client()
    if request.method == 'DELETE':
        resultado = db.table('categorias').update({'activo': False}).eq('id', categoria_id).execute()
    else:
        data = datos_json()
        campos = {'nombre': texto(data, 'nombre', obligatorio=True, limite=50),
                  'descripcion': texto(data, 'descripcion')}
        if 'activo' in data:
            if type(data['activo']) is not bool:
                raise ValueError('Activo debe ser booleano.')
            campos['activo'] = data['activo']
        if categoria_id is None:
            resultado = db.table('categorias').insert(campos).execute()
        else:
            resultado = db.table('categorias').update(campos).eq('id', categoria_id).execute()
    if not resultado.data:
        return jsonify({'status': 'error', 'mensaje': 'Categoría no encontrada.'}), 404
    return jsonify({'status': 'success', 'data': resultado.data[0]}), 201 if categoria_id is None else 200


@app.get('/api/inventario')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def listar_inventario(usuario_actual):
    # Incluye productos sin inventario para que puedan inicializarse formalmente.
    return pagina_consulta(get_supabase_client().table('productos').select(
        'id,nombre,tamano,activo,inventario(stock_actual,stock_minimo,actualizado_en)').order('id'))


@app.put('/api/inventario/<int:producto_id>')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def guardar_inventario(usuario_actual, producto_id):
    data = datos_json()
    esperado = data.get('stock_esperado')
    if esperado is not None:
        esperado = entero(esperado, 'stock_esperado', minimo=0)
    resultado = get_supabase_client().rpc('ajustar_inventario', {
        'p_producto': producto_id, 'p_stock': entero(data.get('stock_actual'), 'stock_actual', minimo=0),
        'p_minimo': entero(data.get('stock_minimo'), 'stock_minimo', minimo=0), 'p_esperado': esperado
    }).execute()
    fila = resultado.data
    notificar_stock([fila])
    return jsonify({'status': 'success', 'data': fila})


@app.put('/api/pedidos/<int:pedido_id>/estado')
@token_requerido
@rol_requerido('ADMINISTRADOR', 'VENDEDOR')
@errores_api
def cambiar_estado(usuario_actual, pedido_id):
    estado = texto(datos_json(), 'estado', obligatorio=True)
    if estado not in ('EN_PREPARACION', 'EN_CAMINO', 'ENTREGADO', 'CANCELADO'):
        raise ValueError('Estado inválido.')
    resultado = get_supabase_client().rpc('cambiar_estado_pedido', {
        'p_actor': usuario_actual['usuario_id'], 'p_pedido': pedido_id, 'p_estado': estado
    }).execute()
    return jsonify({'status': 'success', 'data': resultado.data})


@app.post('/api/ventas')
@token_requerido
@rol_requerido('ADMINISTRADOR', 'VENDEDOR')
@errores_api
def crear_venta(usuario_actual):
    data = datos_json()
    metodo = metodo_validado(data)
    if 'pedido_id' in data:
        nombre = 'registrar_venta'
        argumentos = {'p_actor': usuario_actual['usuario_id'],
                      'p_pedido': entero(data['pedido_id'], 'pedido_id'), 'p_metodo': metodo}
    else:
        nombre = 'venta_directa'
        argumentos = {'p_actor': usuario_actual['usuario_id'],
                      'p_items': items_validados(data.get('items')), 'p_metodo': metodo}
    resultado = get_supabase_client().rpc(nombre, argumentos).execute()
    if nombre == 'venta_directa':
        notificar_pedido({'id': resultado.data['pedido_id'], 'total': resultado.data['venta']['total'],
                          'estado': 'ENTREGADO'}, get_supabase_client)
    return jsonify({'status': 'success', 'data': resultado.data}), 201


@app.get('/api/ventas')
@token_requerido
@rol_requerido('ADMINISTRADOR', 'VENDEDOR')
@errores_api
def listar_ventas(usuario_actual):
    rango = rango_consulta_obligatorio()
    consulta = get_supabase_client().table('ventas').select('*,usuarios(nombre)').gte(
        'fecha_venta', rango['p_desde']).lt('fecha_venta', rango['p_hasta']).order('id', desc=True)
    # El vendedor consulta sus ventas; el administrador puede consultar todas.
    if 'ADMINISTRADOR' not in usuario_actual['roles']:
        consulta = consulta.eq('vendedor_id', usuario_actual['usuario_id'])
    return pagina_consulta(consulta)


@app.get('/api/usuarios')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def listar_usuarios(usuario_actual):
    email = request.args.get('email', '').strip().lower()
    if len(email) > 150 or any(c.isspace() or c in '%*\\' for c in email):
        raise ValueError('Busque por correo o parte del correo, sin espacios ni comodines.')
    consulta = get_supabase_client().table('usuarios').select(
        'id,nombre,email,roles,telefono,creado_en').order('id')
    if email:
        # Tratar el guion bajo como carácter literal, no como comodín SQL.
        consulta = consulta.ilike('email', '%' + email.replace('_', '\\_') + '%')
    return pagina_consulta(consulta)


@app.put('/api/usuarios/<int:usuario_id>/roles')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def guardar_roles(usuario_actual, usuario_id):
    roles = validar_roles(datos_json().get('roles'))
    resultado = get_supabase_client().rpc('cambiar_roles', {
        'p_actor': usuario_actual['usuario_id'], 'p_usuario': usuario_id, 'p_roles': roles
    }).execute()
    return jsonify({'status': 'success', 'data': resultado.data})


def rango_reporte(desde=None, hasta=None):
    hoy = datetime.datetime.now(ZoneInfo('America/La_Paz')).date()
    try:
        inicio = datetime.date.fromisoformat(desde) if desde else hoy - datetime.timedelta(days=6)
        fin = datetime.date.fromisoformat(hasta) if hasta else hoy
    except (TypeError, ValueError):
        raise ValueError('Fechas inválidas; use AAAA-MM-DD.') from None
    if fin < inicio or (fin - inicio).days > 365:
        raise ValueError('El rango debe ser válido y no superar 366 días.')
    zona = ZoneInfo('America/La_Paz')
    return {'p_desde': datetime.datetime.combine(inicio, datetime.time.min, zona).isoformat(),
            'p_hasta': datetime.datetime.combine(fin + datetime.timedelta(days=1), datetime.time.min, zona).isoformat()}


def rango_consulta_obligatorio():
    desde, hasta = request.args.get('desde'), request.args.get('hasta')
    if not desde or not hasta:
        raise ValueError('Seleccione las fechas Desde y Hasta para consultar.')
    return rango_reporte(desde, hasta)


@app.get('/api/reportes/ventas')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def reportes(usuario_actual):
    rango = rango_consulta_obligatorio()
    resultado = get_supabase_client().rpc('reporte_ventas', rango).execute()
    return jsonify({'status': 'success', 'data': resultado.data})


@app.get('/api/integraciones')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def estado_integraciones(usuario_actual):
    from integrations import telegram_configurado
    return jsonify({'status': 'success', 'data': {
        'telegram': bool(telegram_configurado()),
        'asistente': bool(os.getenv('ASSISTANT_ENABLED') == '1' and os.getenv('OPENAI_API_KEY') and os.getenv('OPENAI_MODEL'))
    }})


@app.post('/api/asistente')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def asistente(usuario_actual):
    data = datos_json()
    mensajes = data.get('mensajes')
    if not isinstance(mensajes, list) or not 1 <= len(mensajes) <= 10:
        raise ValueError('Envíe entre 1 y 10 mensajes.')
    for mensaje in mensajes:
        if not isinstance(mensaje, dict) or mensaje.get('role') not in ('user', 'assistant'):
            raise ValueError('Mensaje inválido.')
        texto(mensaje, 'content', obligatorio=True, limite=2000 if mensaje['role'] == 'user' else 10000)
    if mensajes[-1]['role'] != 'user':
        raise ValueError('El último mensaje debe ser del usuario.')
    db = get_supabase_client()
    herramientas = {
        'consultar_catalogo': {'descripcion': 'Catálogo actual de hasta 100 opciones con tamaños y precios.',
            'consultar': lambda: db.table('productos').select('id,nombre,tamano,precio,activo').order('id').limit(100).execute().data},
        'consultar_inventario': {'descripcion': 'Stock y mínimos de hasta 100 productos.',
            'consultar': lambda: db.table('inventario').select('stock_actual,stock_minimo,productos(nombre,tamano)').order('producto_id').limit(100).execute().data},
        'consultar_ventas': {'descripcion': 'Ventas cobradas y consumo de productos en los últimos siete días.',
            'consultar': lambda: db.rpc('reporte_ventas', rango_reporte()).execute().data}
    }
    try:
        respuesta = responder_asistente(mensajes, herramientas)
    except RuntimeError as error:
        return jsonify({'status': 'error', 'mensaje': str(error)}), 503
    return jsonify({'status': 'success', 'respuesta': respuesta})

if __name__ == '__main__':
    puerto = int(os.getenv('PORT', 5000))
    app.run(debug=os.getenv('FLASK_DEBUG') == '1', port=puerto)
