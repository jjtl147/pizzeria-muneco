import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno desde backend/.env
load_dotenv()

app = Flask(__name__)
# Habilitar CORS para permitir peticiones desde el frontend (React/Vite)
CORS(app)

# Configuración y conexión con Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

def get_supabase_client() -> Client:
    """
    Inicializa y retorna la instancia del cliente de Supabase.
    Limpia y valida la URL base y la clave de acceso.
    """
    url = os.getenv('SUPABASE_URL', '').strip()
    key = os.getenv('SUPABASE_KEY', '').strip()

    if not url or not key or 'tu-proyecto' in url:
        raise ValueError("Las credenciales de Supabase no están configuradas correctamente en el archivo .env")

    # Asegurar que la URL sea la raíz base (remover /rest/v1 o barras finales)
    if '/rest/v1' in url:
        url = url.split('/rest/v1')[0]
    url = url.rstrip('/')

    return create_client(url, key)

# ==========================================
# RUTAS / ENDPOINTS DE LA API
# ==========================================

@app.route('/', methods=['GET'])
def index():
    """
    Ruta raíz para verificar que el servidor esté activo y documentar endpoints.
    """
    return jsonify({
        "status": "success",
        "mensaje": "API Pizzería Muñeco - Backend Flask activo",
        "endpoints_disponibles": [
            "/api/status",
            "/api/productos"
        ]
    }), 200

@app.route('/api/status', methods=['GET'])
def status():
    """
    Endpoint de verificación del estado del servidor.
    """
    return jsonify({
        "status": "success",
        "mensaje": "Backend de Flask funcionando correctamente"
    }), 200

@app.route('/api/productos', methods=['GET'])
def obtener_productos():
    """
    Endpoint para obtener el listado de productos desde la base de datos (Supabase).
    Retorna la lista de productos en formato JSON.
    """
    try:
        supabase = get_supabase_client()
        # Consulta flexible de todos los campos de la tabla 'productos'
        response = supabase.table('productos').select('*').execute()

        # Si los datos tienen campo 'activo', filtramos los activos; si no, devolvemos todos
        productos = response.data or []
        if productos and 'activo' in productos[0]:
            productos = [p for p in productos if p.get('activo') is not False]

        return jsonify({
            "status": "success",
            "total": len(productos),
            "data": productos
        }), 200

    except ValueError as val_err:
        print(f"[ERROR CONFIG] {val_err}")
        return jsonify({
            "status": "error",
            "mensaje": str(val_err)
        }), 500
    except Exception as e:
        print(f"[ERROR BD /api/productos]: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "mensaje": f"Error al consultar la base de datos: {str(e)}"
        }), 500

if __name__ == '__main__':
    puerto = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=puerto)