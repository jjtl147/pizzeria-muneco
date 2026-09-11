# Planificación Scrum — Sistema Web para Pizzería
**Proyecto de titulación — Ingeniería de Sistemas**

**Fecha de inicio de planificación:** 4 de septiembre de 2026
**Fecha objetivo de entrega (MVP completo):** 10 de noviembre de 2026
**Duración total:** 67 días (~9.5 semanas)

> Nota: la fecha límite se ajustó de 20 al 10 de noviembre de 2026, por lo que
> los sprints posteriores al Sprint 1 se comprimieron de 14 a 12 días, y el
> buffer final se redujo de 7 a 5 días, manteniendo el mismo alcance funcional.

---

## Fase 0 — Configuración inicial y funcionalidades base (previo al inicio formal de Scrum)

Antes de adoptar la metodología Scrum de forma estructurada, se desarrollaron las siguientes funcionalidades base, registradas en el historial de control de versiones (Git/GitHub):

- Inicialización del proyecto frontend (React + Vite + pnpm)
- Configuración de Bootstrap y React Bootstrap
- Estructura de rutas con React Router (Home, Catálogo, Carrito, Login)
- Diseño del layout base (Navbar + Outlet)
- Implementación del catálogo de productos con datos de ejemplo (mock data)
- Implementación del carrito de compras funcional, utilizando el patrón
  Context API de React (Context + Provider + hook useContext) para el
  manejo de estado global sin necesidad de librerías externas (Redux/Zustand),
  en línea con las restricciones de arquitectura definidas para el proyecto
- Configuración de control de versiones (Git) y repositorio remoto en GitHub
- Migración del entorno de desarrollo de Windows a Linux (Pop!_OS)

Esta fase corresponde al periodo previo al 4 de septiembre de 2026, y su
evidencia de desarrollo se encuentra documentada en el historial de commits
del repositorio.

---

## Resumen de avance al inicio de la planificación

### Frontend
| Módulo | Estado | % |
|---|---|---|
| Estructura base (Vite, rutas, navbar) | Completo | 100% |
| Catálogo de productos (mock data) | Completo | 100% |
| Carrito de compras (Context API) | Completo | 100% |
| Página Home (contenido real) | En progreso | 15% |
| Página Login (formulario real) | En progreso | 10% |
| Conexión a backend real | No iniciado | 0% |

**Frontend total (fase cliente): ~55%**

### Backend
| Módulo | Estado | % |
|---|---|---|
| Estructura Flask | No iniciado | 0% |
| API REST (endpoints) | No iniciado | 0% |
| Conexión a Supabase/PostgreSQL | No iniciado | 0% |
| Autenticación y roles | No iniciado | 0% |

**Backend total: 0%**

### Avance general estimado del proyecto: ~11%

---

## Sprints planificados

### Sprint 1 — 4 al 18 de septiembre
**Objetivo:** Cerrar frontend cliente base + iniciar backend

- [ ] Completar Home y Login (contenido visual completo)
- [x] Estructura de carpetas Flask (app/, routes/, models/) — versión inicial simple (app.py) con entorno virtual y servidor de desarrollo funcional; se reorganizará en subcarpetas cuando la lógica del backend crezca
- [ ] Configurar conexión Flask ↔ Supabase (.env)
- [ ] Diseñar esquema de base de datos (usuarios, productos, categorías, pedidos, inventario)
- [ ] Endpoint GET /api/productos funcionando con datos reales

### Sprint 2 — 18 al 30 de septiembre
**Objetivo:** API REST funcional + autenticación backend

- [ ] Endpoints CRUD de productos
- [ ] Endpoint POST /api/pedidos
- [ ] Reemplazar products.js mock por consumo real vía Axios
- [ ] Sistema de autenticación en Flask (JWT + hash de contraseñas)
- [ ] Endpoints POST /api/auth/registro y POST /api/auth/login

### Sprint 3 — 30 de septiembre al 12 de octubre
**Objetivo:** Autenticación funcional en frontend + pedidos del cliente

- [ ] Formulario de Login/Registro conectado al backend real
- [ ] Manejo de sesión (token) y rutas protegidas en React Router
- [ ] Página "Mis pedidos" (historial + estado)
- [ ] Cerrar sesión funcional

### Sprint 4 — 12 al 24 de octubre
**Objetivo:** Panel administrativo — gestión operativa

- [ ] Layout del panel admin (rutas protegidas para rol administrador)
- [ ] CRUD visual de productos y categorías
- [ ] Gestión de inventario (stock, alertas de stock bajo)
- [ ] Gestión de pedidos (cambio de estados)

### Sprint 5 — 24 de octubre al 5 de noviembre
**Objetivo:** Reportes + integración Telegram y n8n

- [ ] Dashboard de ventas/estadísticas
- [ ] Configuración de n8n para automatización de flujos con Telegram
- [ ] Bot de Telegram: notificaciones (nuevo pedido, stock bajo)
- [ ] Asistente conversacional básico (consultas simples al backend)

### Buffer final — 5 al 10 de noviembre
**Objetivo:** Estabilización y documentación

- [ ] Pruebas de extremo a extremo
- [ ] Corrección de errores encontrados
- [ ] Preparación de documentación para sustentación

---

## Notas de metodología

Este proyecto sigue un enfoque Scrum adaptado para desarrollo individual:
- Sprints de 2 semanas de duración
- Revisión de avance al cierre de cada sprint, con reorganización del backlog siguiente según el progreso real
- El backlog de cada sprint puede ajustarse; el Sprint Goal (objetivo general) se mantiene como guía principal
- Funcionalidades no contempladas en este plan (mejoras post-MVP) se gestionan por separado, fuera del alcance de los 100% funcionales previstos para el 20 de noviembre
