# Informe de Avance — Cierre del Sprint 1
**Proyecto de Titulación — Ingeniería de Sistemas**  
**Sistema Web para Pizzería Muñeco**  
**Fecha:** 30 de septiembre de 2026  
**Estado:** Sprint 1 Completado al 100% ✅

---

## 1. Resumen Ejecutivo

Durante este sprint se cumplieron satisfactoriamente los dos ejes principales planificados:
1. **Consolidación visual del Frontend para el rol Cliente:** Finalización de las páginas de inicio (`Home.jsx`), inicio de sesión (`Login.jsx`) y componente visual del carrito (`Carrito.jsx`).
2. **Infraestructura inicial del Backend y Persistencia:** Configuración del entorno de desarrollo con Python y Flask, diseño del esquema relacional de base de datos en PostgreSQL (Supabase), conexión segura mediante variables de entorno y habilitación del primer endpoint de datos reales (`GET /api/productos`).

---

## 2. Detalle de Actividades y Entregables Técnicos

### A. Frontend (React 19 + Bootstrap)
* **Página de Inicio (`src/pages/Home.jsx`):**
  * *Hero Section:* Título principal, llamado a la acción y navegación hacia `/catalogo` mediante `react-router-dom`.
  * *Sección "¿Cómo funciona?":* Flujo explicativo de 3 pasos para el usuario (Selección, Carrito, Entrega) utilizando tarjetas de React Bootstrap.
  * *Vitrina de Productos Populares:* Exhibición de pizzas destacadas consumiendo datos base.
* **Página de Autenticación (`src/pages/Login.jsx`):**
  * Formulario centrado con campos de correo y contraseña en contenedor `Card`.
  * Enlace para futuro registro y manejador `onSubmit` con prevención de recarga por defecto.
* **Vista del Carrito (`src/pages/Carrito.jsx` - `CarritoVista`):**
  * Componente presentacional desacoplado con tabla responsiva (`striped`, `bordered`, `hover`).
  * Controles de cantidad (`+` / `-`), botón para eliminar ítem y resumen totalizador destacado.
  * Manejo del estado visual cuando el carrito se encuentra vacío.

---

### B. Base de Datos (PostgreSQL en Supabase)
* **Diseño del Esquema Relacional (`backend/schema.sql`):**
  * `categorias`: Gestión de tipos de productos.
  * `usuarios`: Soporte para roles (`CLIENTE`, `ADMINISTRADOR`) y almacenamiento de contraseñas con hash.
  * `productos`: Catálogo con relaciones foráneas a categorías y validación de precios no negativos.
  * `inventario`: Control de stock actual y niveles mínimos de alerta por producto.
  * `pedidos` y `detalle_pedidos`: Estructura para registrar órdenes con estados y cálculo de subtotales.
* **Integridad de datos:** Aplicación de llaves primarias autoincrementales (`SERIAL`), llaves foráneas (`REFERENCES`), restricciones `CHECK` y valores por defecto.

---

### C. Backend (Python + Flask)
* **Estructura y Servidor Base (`backend/app.py`):**
  * Configuración de entorno virtual (`venv`) con dependencias registradas en `requirements.txt`.
  * Habilitación de **CORS** (`flask-cors`) para permitir la comunicación cruzada con el frontend de Vite.
  * Manejo de rutas principales:
    * `GET /`: Documentación inicial de endpoints disponibles.
    * `GET /api/status`: Health check del servidor.
    * `GET /api/productos`: Consulta directa a la tabla `productos` en Supabase filtrando ítems activos y devolviendo JSON estructurado.
* **Seguridad y Variables de Entorno:**
  * Uso de `python-dotenv` para cargar credenciales de forma desacoplada.
  * Implementación de archivo plantilla `backend/.env.example` para documentación.
  * Sanitización automática de URLs y control estricto de excepciones ante errores de conexión.

---

## 3. Decisiones Técnicas y Justificación Académica

| Decisión Técnica | Justificación para Defensa de Grado |
|---|---|
| **PostgreSQL vía Supabase** | Motor relacional robusto que garantiza integridad referencial (ACID), permitiendo centrar el esfuerzo en el desarrollo de la API REST sin complejidad de infraestructura local. |
| **Separación de Configuración (`.env`)** | Cumplimiento del principio *Twelve-Factor App* (Factor III: Configuración), evitando almacenar credenciales en el código fuente. |
| **Componente Visual Desacoplado** | Aplicación del patrón *Container/Presentational*, facilitando pruebas y modularidad antes de conectar el Context API. |
| **Flask + Flask-CORS** | Microframework ligero que evita sobreingeniería innecesaria y facilita explicar cada línea de código en sustentación. |

---

## 4. Estado del Proyecto al Cierre del Sprint 1

* **Frontend (Vistas Cliente):** 80% completado (listo para integración con API).
* **Backend Base & BD:** 35% completado (servidor activo, BD creada y endpoint inicial funcional).
* **Avance General del Proyecto:** ~28%.

---

## 5. Próximos Pasos (Sprint 2: 18 al 30 de Septiembre)

1. Implementar endpoints CRUD completos para productos en Flask.
2. Crear endpoint `POST /api/pedidos` para procesamiento de compras.
3. Conectar el catálogo del Frontend mediante peticiones HTTP reales usando **Axios**.
4. Implementar el módulo de autenticación con JWT y hashing de contraseñas (`Werkzeug` / `bcrypt`).

