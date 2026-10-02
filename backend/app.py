import os
import datetime
from functools import wraps
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
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'pizzeria_muneco_secreto_super_seguro_jwt_2026')

def get_supabase_client() -> Client:
    url = os.getenv('SUPABASE_URL', '').strip()
    key = os.getenv('SUPABASE_KEY', '').strip()

    if not url or not key or 'tu-proyecto' in url:
        raise ValueError("Las credenciales de Supabase no están configuradas correctamente en el archivo .env")

    if '/rest/v1' in url:
        url = url.split('/rest/v1')[0]
    url = url.rstrip('/')

    return create_client(url, key)

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
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            usuario_actual = payload
        except jwt.ExpiredSignatureError:
            return jsonify({
                "status": "error",
                "mensaje": "El token ha expirado. Inicie sesión nuevamente."
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "status": "error",
                "mensaje": "Token de autenticación inválido."
            }), 401

        return f(usuario_actual, *args, **kwargs)
    return decorador

def admin_requerido(f):
    @wraps(f)
    def decorador(usuario_actual, *args, **kwargs):
        if usuario_actual.get('rol') != 'ADMINISTRADOR':
            return jsonify({
                "status": "error",
                "mensaje": "Acceso denegado. Se requieren permisos de ADMINISTRADOR."
            }), 403
        return f(usuario_actual, *args, **kwargs)
    return decorador

# ==========================================
# RUTAS DE ESTADO Y DOCUMENTACIÓN
# ==========================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "success",
        "mensaje": "API Pizzería Muñeco - Backend Flask activo",
        "endpoints_disponibles": [
            {"metodo": "GET", "ruta": "/api/status", "descripcion": "Health check"},
            {"metodo": "GET", "ruta": "/api/productos", "descripcion": "Listar productos activos"},
            {"metodo": "GET", "ruta": "/api/productos/<id>", "descripcion": "Ver detalle de producto"},
            {"metodo": "POST", "ruta": "/api/productos", "descripcion": "Crear producto (Admin)"},
            {"metodo": "PUT", "ruta": "/api/productos/<id>", "descripcion": "Actualizar producto (Admin)"},
            {"metodo": "DELETE", "ruta": "/api/productos/<id>", "descripcion": "Eliminar producto (Admin)"},
            {"metodo": "POST", "ruta": "/api/auth/registro", "descripcion": "Registro de clientes"},
            {"metodo": "POST", "ruta": "/api/auth/login", "descripcion": "Inicio de sesión (retorna JWT)"},
            {"metodo": "GET", "ruta": "/api/auth/perfil", "descripcion": "Perfil de usuario (Auth)"},
            {"metodo": "POST", "ruta": "/api/pedidos", "descripcion": "Crear nuevo pedido (Auth)"},
            {"metodo": "GET", "ruta": "/api/pedidos/mis-pedidos", "descripcion": "Historial de pedidos del cliente (Auth)"},
            {"metodo": "GET", "ruta": "/api/pedidos", "descripcion": "Listar todos los pedidos (Admin)"}
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
        data = request.get_json() or {}
        nombre = data.get('nombre', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        telefono = data.get('telefono', '').strip()
        direccion = data.get('direccion', '').strip()

        if not nombre or not email or not password:
            return jsonify({
                "status": "error",
                "mensaje": "Los campos 'nombre', 'email' y 'password' son obligatorios."
            }), 400

        if len(password) < 6:
            return jsonify({
                "status": "error",
                "mensaje": "La contraseña debe tener al menos 6 caracteres."
            }), 400

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
            'rol': 'CLIENTE',
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
                "rol": usuario_creado.get('rol')
            }
        }), 201

    except Exception as e:
        print(f"[ERROR /api/auth/registro]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al procesar el registro: {str(e)}"
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        if not email or not password:
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
            'rol': usuario.get('rol'),
            'exp': expiracion
        }

        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

        return jsonify({
            "status": "success",
            "mensaje": "Inicio de sesión exitoso.",
            "token": token,
            "usuario": {
                "id": usuario.get('id'),
                "nombre": usuario.get('nombre'),
                "email": usuario.get('email'),
                "rol": usuario.get('rol'),
                "telefono": usuario.get('telefono'),
                "direccion": usuario.get('direccion')
            }
        }), 200

    except Exception as e:
        print(f"[ERROR /api/auth/login]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al procesar el inicio de sesión: {str(e)}"
        }), 500

@app.route('/api/auth/perfil', methods=['GET'])
@token_requerido
def perfil(usuario_actual):
    try:
        supabase = get_supabase_client()
        resultado = supabase.table('usuarios')\
            .select('id, nombre, email, rol, telefono, direccion, creado_en')\
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

    except Exception as e:
        print(f"[ERROR /api/auth/perfil]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al obtener perfil: {str(e)}"
        }), 500

# ==========================================
# MÓDULO CRUD DE PRODUCTOS
# ==========================================

@app.route('/api/productos', methods=['GET'])
def obtener_productos():
    try:
        supabase = get_supabase_client()
        response = supabase.table('productos').select('*').execute()

        productos = response.data or []
        if productos and 'activo' in productos[0]:
            productos = [p for p in productos if p.get('activo') is not False]

        return jsonify({
            "status": "success",
            "total": len(productos),
            "data": productos
        }), 200

    except Exception as e:
        print(f"[ERROR /api/productos GET]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al consultar productos: {str(e)}"
        }), 500

@app.route('/api/productos/<int:producto_id>', methods=['GET'])
def obtener_producto_detalle(producto_id):
    try:
        supabase = get_supabase_client()
        response = supabase.table('productos').select('*').eq('id', producto_id).execute()

        if not response.data or len(response.data) == 0:
            return jsonify({
                "status": "error",
                "mensaje": "Producto no encontrado."
            }), 404

        return jsonify({
            "status": "success",
            "data": response.data[0]
        }), 200

    except Exception as e:
        print(f"[ERROR /api/productos/<id> GET]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al consultar el producto: {str(e)}"
        }), 500

@app.route('/api/productos', methods=['POST'])
@token_requerido
@admin_requerido
def crear_producto(usuario_actual):
    try:
        data = request.get_json() or {}
        nombre = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '').strip()
        precio = data.get('precio')
        categoria_id = data.get('categoria_id')
        imagen = data.get('imagen', '').strip()

        if not nombre or precio is None:
            return jsonify({
                "status": "error",
                "mensaje": "Los campos 'nombre' y 'precio' son obligatorios."
            }), 400

        try:
            precio_num = float(precio)
            if precio_num < 0:
                raise ValueError()
        except ValueError:
            return jsonify({
                "status": "error",
                "mensaje": "El precio debe ser un número válido mayor o igual a 0."
            }), 400

        supabase = get_supabase_client()

        nuevo_producto = {
            'nombre': nombre,
            'descripcion': descripcion if descripcion else None,
            'precio': precio_num,
            'categoria_id': categoria_id if categoria_id else None,
            'imagen': imagen if imagen else 'https://placehold.co/400x300?text=Pizza',
            'activo': True
        }

        resultado = supabase.table('productos').insert(nuevo_producto).execute()

        if not resultado.data:
            raise Exception("No se pudo insertar el producto en la base de datos.")

        producto_creado = resultado.data[0]

        stock_inicial = data.get('stock_inicial', 50)
        try:
            supabase.table('inventario').insert({
                'producto_id': producto_creado['id'],
                'stock_actual': int(stock_inicial),
                'stock_minimo': 10
            }).execute()
        except Exception as inv_err:
            print(f"[WARN] No se pudo inicializar inventario: {inv_err}")

        return jsonify({
            "status": "success",
            "mensaje": "Producto creado exitosamente.",
            "data": producto_creado
        }), 201

    except Exception as e:
        print(f"[ERROR /api/productos POST]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al crear producto: {str(e)}"
        }), 500

@app.route('/api/productos/<int:producto_id>', methods=['PUT'])
@token_requerido
@admin_requerido
def actualizar_producto(usuario_actual, producto_id):
    try:
        data = request.get_json() or {}
        supabase = get_supabase_client()

        existente = supabase.table('productos').select('id').eq('id', producto_id).execute()
        if not existente.data or len(existente.data) == 0:
            return jsonify({
                "status": "error",
                "mensaje": "El producto no existe."
            }), 404

        campos_actualizar = {}
        if 'nombre' in data and data['nombre'].strip():
            campos_actualizar['nombre'] = data['nombre'].strip()
        if 'descripcion' in data:
            campos_actualizar['descripcion'] = data['descripcion'].strip()
        if 'precio' in data:
            try:
                precio_num = float(data['precio'])
                if precio_num < 0:
                    raise ValueError()
                campos_actualizar['precio'] = precio_num
            except ValueError:
                return jsonify({
                    "status": "error",
                    "mensaje": "El precio debe ser un número positivo."
                }), 400
        if 'categoria_id' in data:
            campos_actualizar['categoria_id'] = data['categoria_id']
        if 'imagen' in data:
            campos_actualizar['imagen'] = data['imagen'].strip()
        if 'activo' in data:
            campos_actualizar['activo'] = bool(data['activo'])

        if not campos_actualizar:
            return jsonify({
                "status": "error",
                "mensaje": "No se enviaron campos válidos para actualizar."
            }), 400

        resultado = supabase.table('productos').update(campos_actualizar).eq('id', producto_id).execute()

        return jsonify({
            "status": "success",
            "mensaje": "Producto actualizado correctamente.",
            "data": resultado.data[0] if resultado.data else {}
        }), 200

    except Exception as e:
        print(f"[ERROR /api/productos/<id> PUT]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al actualizar el producto: {str(e)}"
        }), 500

@app.route('/api/productos/<int:producto_id>', methods=['DELETE'])
@token_requerido
@admin_requerido
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

    except Exception as e:
        print(f"[ERROR /api/productos/<id> DELETE]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al eliminar producto: {str(e)}"
        }), 500

# ==========================================
# MÓDULO DE PEDIDOS
# ==========================================

@app.route('/api/pedidos', methods=['POST'])
@token_requerido
def crear_pedido(usuario_actual):
    try:
        data = request.get_json() or {}
        direccion_entrega = data.get('direccion_entrega', '').strip()
        telefono_contacto = data.get('telefono_contacto', '').strip()
        metodo_pago = data.get('metodo_pago', 'EFECTIVO').strip().upper()
        items = data.get('items', [])

        if not direccion_entrega:
            return jsonify({
                "status": "error",
                "mensaje": "La dirección de entrega es obligatoria."
            }), 400

        if not items or not isinstance(items, list) or len(items) == 0:
            return jsonify({
                "status": "error",
                "mensaje": "El pedido debe contener al menos un producto en 'items'."
            }), 400

        total_calculado = 0.0
        detalles_preparados = []
        supabase = get_supabase_client()

        for item in items:
            producto_id = item.get('producto_id')
            cantidad = item.get('cantidad', 0)

            if not producto_id or cantidad <= 0:
                return jsonify({
                    "status": "error",
                    "mensaje": "Cada ítem debe tener un 'producto_id' válido y cantidad > 0."
                }), 400

            producto_bd = supabase.table('productos').select('precio, activo').eq('id', producto_id).execute()

            if not producto_bd.data or len(producto_bd.data) == 0:
                return jsonify({
                    "status": "error",
                    "mensaje": f"El producto con ID {producto_id} no existe."
                }), 400

            precio_real = float(producto_bd.data[0]['precio'])
            subtotal = round(cantidad * precio_real, 2)
            total_calculado += subtotal

            detalles_preparados.append({
                'producto_id': producto_id,
                'cantidad': cantidad,
                'precio_unitario': precio_real,
                'subtotal': subtotal
            })

        total_calculado = round(total_calculado, 2)

        nuevo_pedido = {
            'usuario_id': usuario_actual['usuario_id'],
            'total': total_calculado,
            'direccion_entrega': direccion_entrega,
            'telefono_contacto': telefono_contacto if telefono_contacto else None,
            'metodo_pago': metodo_pago,
            'estado': 'PENDIENTE'
        }

        res_pedido = supabase.table('pedidos').insert(nuevo_pedido).execute()
        if not res_pedido.data or len(res_pedido.data) == 0:
            raise Exception("No se pudo registrar la cabecera del pedido en la base de datos.")

        pedido_creado = res_pedido.data[0]
        pedido_id = pedido_creado['id']

        for detalle in detalles_preparados:
            detalle['pedido_id'] = pedido_id

        res_detalles = supabase.table('detalle_pedidos').insert(detalles_preparados).execute()

        return jsonify({
            "status": "success",
            "mensaje": "Pedido registrado exitosamente.",
            "data": {
                "pedido": pedido_creado,
                "detalles": res_detalles.data
            }
        }), 201

    except Exception as e:
        print(f"[ERROR /api/pedidos POST]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al procesar el pedido: {str(e)}"
        }), 500

@app.route('/api/pedidos/mis-pedidos', methods=['GET'])
@token_requerido
def mis_pedidos(usuario_actual):
    try:
        supabase = get_supabase_client()
        resultado = supabase.table('pedidos')\
            .select('id, fecha_pedido, estado, total, direccion_entrega, metodo_pago, detalle_pedidos(*, productos(nombre, imagen))')\
            .eq('usuario_id', usuario_actual['usuario_id'])\
            .order('fecha_pedido', desc=True)\
            .execute()

        return jsonify({
            "status": "success",
            "total": len(resultado.data or []),
            "data": resultado.data or []
        }), 200

    except Exception as e:
        print(f"[ERROR /api/pedidos/mis-pedidos GET]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al consultar el historial de pedidos: {str(e)}"
        }), 500

@app.route('/api/pedidos', methods=['GET'])
@token_requerido
@admin_requerido
def listar_todos_los_pedidos(usuario_actual):
    try:
        supabase = get_supabase_client()
        resultado = supabase.table('pedidos')\
            .select('id, fecha_pedido, estado, total, direccion_entrega, metodo_pago, usuarios(nombre, email), detalle_pedidos(*, productos(nombre))')\
            .order('fecha_pedido', desc=True)\
            .execute()

        return jsonify({
            "status": "success",
            "total": len(resultado.data or []),
            "data": resultado.data or []
        }), 200

    except Exception as e:
        print(f"[ERROR /api/pedidos GET]: {str(e)}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al consultar pedidos globales: {str(e)}"
        }), 500

if __name__ == '__main__':
    puerto = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=puerto)