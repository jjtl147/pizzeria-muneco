import os
import datetime
from functools import wraps
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
from integrations import notificar_pedido, notificar_stock, responder_asistente
from postgrest.exceptions import APIError
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '').strip()

def get_supabase_client() -> Client:
    url = os.getenv('SUPABASE_URL', '').strip()
    key = os.getenv('SUPABASE_KEY', '').strip()

    if not url or not key or 'tu-proyecto' in url:
        raise RuntimeError("Las credenciales de Supabase no están configuradas correctamente en el archivo .env")

    if '/rest/v1' in url:
        url = url.split('/rest/v1')[0]
    url = url.rstrip('/')

    return create_client(url, key)

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


def clave_jwt():
    if len(JWT_SECRET_KEY) < 32:
        raise RuntimeError("Configure JWT_SECRET_KEY con al menos 32 caracteres aleatorios.")
    return JWT_SECRET_KEY


# ==========================================
# MIDDLEWARES / DECORADORES DE AUTENTICACIÓN
# ==========================================

def token_requerido(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            partes = auth_header.split()
            if len(partes) == 2 and partes[0] == 'Bearer':
                token = partes[1]

        if not token:
            return jsonify({
                "status": "error",
                "mensaje": "Token de autenticación requerido. Inicie sesión para continuar."
            }), 401

        try:
            payload = jwt.decode(token, clave_jwt(), algorithms=['HS256'],
                                 options={'require': ['exp', 'usuario_id', 'roles']})
            entero(payload.get('usuario_id'), 'usuario_id')
            validar_roles(payload.get('roles'))
            usuario = cargar_usuario(payload['usuario_id'])
            if not usuario:
                return jsonify({'status': 'error', 'mensaje': 'La cuenta ya no existe.'}), 401
            usuario_actual = {**usuario, 'usuario_id': usuario['id']}
            validar_roles(usuario_actual.get('roles'))
        except jwt.ExpiredSignatureError:
            return jsonify({
                "status": "error",
                "mensaje": "El token ha expirado. Inicie sesión nuevamente."
            }), 401
        except (jwt.InvalidTokenError, ValueError):
            return jsonify({
                "status": "error",
                "mensaje": "Token de autenticación inválido."
            }), 401

        except RuntimeError:
            return jsonify({"status": "error", "mensaje": "Autenticación no configurada en el servidor."}), 503
        except Exception:
            app.logger.exception('No se pudo verificar la sesión')
            return jsonify({'status': 'error', 'mensaje': 'No se pudo verificar la sesión. Intente nuevamente.'}), 503

        return f(usuario_actual, *args, **kwargs)
    return decorador

ROLES = {'CLIENTE', 'VENDEDOR', 'ADMINISTRADOR'}
METODOS_PAGO = {'EFECTIVO', 'QR', 'TARJETA'}


def validar_roles(roles):
    if not isinstance(roles, list) or not roles or any(not isinstance(r, str) or r not in ROLES for r in roles):
        raise ValueError('Seleccione al menos un rol válido.')
    if len(roles) != len(set(roles)):
        raise ValueError('Los roles no deben repetirse.')
    return roles


def cargar_usuario(usuario_id):
    resultado = get_supabase_client().table('usuarios').select(
        'id,nombre,email,roles,telefono,direccion,creado_en').eq('id', usuario_id).execute()
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

@app.route('/api/auth/registro', methods=['POST'])
def registro():
    try:
        data = datos_json()
        nombre = texto(data, 'nombre', limite=100)
        email = texto(data, 'email', limite=150).lower()
        password = texto(data, 'password', recortar=False)
        telefono = texto(data, 'telefono', limite=20)
        direccion = texto(data, 'direccion')

        if not nombre or not email or not password.strip():
            return jsonify({
                "status": "error",
                "mensaje": "Los campos 'nombre', 'email' y 'password' son obligatorios."
            }), 400

        if len(password) < 6:
            return jsonify({
                "status": "error",
                "mensaje": "La contraseña debe tener al menos 6 caracteres."
            }), 400

        if email.count('@') != 1 or any(c.isspace() for c in email) or not all(email.split('@')):
            raise ValueError('El correo electrónico no es válido.')

        supabase = get_supabase_client()

        usuario_existente = supabase.table('usuarios').select('id').eq('email', email).execute()

        if usuario_existente.data and len(usuario_existente.data) > 0:
            return jsonify({
                "status": "error",
                "mensaje": "El correo electrónico ya se encuentra registrado."
            }), 400

        password_hash = generate_password_hash(password)

        nuevo_usuario = {
            'nombre': nombre,
            'email': email,
            'password_hash': password_hash,
            'roles': ['CLIENTE'],
            'telefono': telefono if telefono else None,
            'direccion': direccion if direccion else None
        }

        resultado = supabase.table('usuarios').insert(nuevo_usuario).execute()

        if not resultado.data:
            raise Exception("No se pudo crear el registro del usuario en la base de datos.")

        usuario_creado = resultado.data[0]

        return jsonify({
            "status": "success",
            "mensaje": "Usuario registrado exitosamente.",
            "data": {
                "id": usuario_creado.get('id'),
                "nombre": usuario_creado.get('nombre'),
                "email": usuario_creado.get('email'),
                "roles": usuario_creado.get('roles')
            }
        }), 201

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/auth/registro]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al procesar el registro. Consulte al administrador si el problema persiste."
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = datos_json()
        email = texto(data, 'email', limite=150).lower()
        password = texto(data, 'password', recortar=False)

        if not email or not password.strip():
            return jsonify({
                "status": "error",
                "mensaje": "Debe proporcionar correo electrónico y contraseña."
            }), 400

        supabase = get_supabase_client()

        resultado = supabase.table('usuarios').select('*').eq('email', email).execute()

        if not resultado.data or len(resultado.data) == 0:
            return jsonify({
                "status": "error",
                "mensaje": "Credenciales inválidas. Verifique su correo o contraseña."
            }), 401

        usuario = resultado.data[0]

        if not check_password_hash(usuario.get('password_hash', ''), password):
            return jsonify({
                "status": "error",
                "mensaje": "Credenciales inválidas. Verifique su correo o contraseña."
            }), 401

        expiracion = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        payload = {
            'usuario_id': usuario.get('id'),
            'nombre': usuario.get('nombre'),
            'email': usuario.get('email'),
            'roles': validar_roles(usuario.get('roles')),
            'exp': expiracion
        }

        token = jwt.encode(payload, clave_jwt(), algorithm='HS256')

        return jsonify({
            "status": "success",
            "mensaje": "Inicio de sesión exitoso.",
            "token": token,
            "usuario": {
                "id": usuario.get('id'),
                "nombre": usuario.get('nombre'),
                "email": usuario.get('email'),
                "roles": usuario.get('roles'),
                "telefono": usuario.get('telefono'),
                "direccion": usuario.get('direccion')
            }
        }), 200

    except ValueError as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"[ERROR /api/auth/login]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": "Error al procesar el inicio de sesión. Consulte al administrador si el problema persiste."
        }), 500

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
    consulta = get_supabase_client().table('ventas').select('*,usuarios(nombre)').order('id', desc=True)
    # El vendedor consulta sus ventas; el administrador puede consultar todas.
    if 'ADMINISTRADOR' not in usuario_actual['roles']:
        consulta = consulta.eq('vendedor_id', usuario_actual['usuario_id'])
    return pagina_consulta(consulta)


@app.get('/api/usuarios')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def listar_usuarios(usuario_actual):
    return pagina_consulta(get_supabase_client().table('usuarios').select(
        'id,nombre,email,roles,telefono,creado_en').order('id'))


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


@app.get('/api/reportes/ventas')
@token_requerido
@rol_requerido('ADMINISTRADOR')
@errores_api
def reportes(usuario_actual):
    resultado = get_supabase_client().rpc('reporte_ventas', rango_reporte(
        request.args.get('desde'), request.args.get('hasta'))).execute()
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
