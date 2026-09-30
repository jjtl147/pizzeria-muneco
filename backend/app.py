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
    Valida que las credenciales no sean las predeterminadas.
    """
    if not SUPABASE_URL or not SUPABASE_KEY or 'tu-proyecto' in SUPABASE_URL:
        raise ValueError("Las credenciales de Supabase no están configuradas correctamente en el archivo .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

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
    Endpoint para obtener el listado de productos activos desde la base de datos (Supabase).
    Retorna la lista de productos en formato JSON.
    """
    try:
        supabase = get_supabase_client()
        # Consulta a la tabla 'productos' filtrando los que están activos y ordenados por id
        response = supabase.table('productos')\
            .select('id, categoria_id, nombre, descripcion, precio, imagen, activo')\
            .eq('activo', True)\
            .order('id')\
            .execute()

        return jsonify({
            "status": "success",
            "total": len(response.data),
            "data": response.data
        }), 200

    except ValueError as val_err:
        # Error cuando faltan credenciales en el archivo .env
        return jsonify({
            "status": "error",
            "mensaje": str(val_err)
        }), 500
    except Exception as e:
        # Error de conexión o consulta a la base de datos
        return jsonify({
            "status": "error",
            "mensaje": f"Error al consultar la base de datos: {str(e)}"
        }), 500

if __name__ == '__main__':
    puerto = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=puerto)