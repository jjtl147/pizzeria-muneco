# Planificación Scrum — Sistema Web para Pizzería
**Proyecto de titulación — Ingeniería de Sistemas**

**Fecha de inicio de planificación:** 4 de septiembre de 2026
**Fecha objetivo de entrega (MVP completo):** 20 de noviembre de 2026
**Duración total:** 11 semanas

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
- [ ] Estructura de carpetas Flask (app/, routes/, models/)
- [ ] Configurar conexión Flask ↔ Supabase (.env)
- [ ] Diseñar esquema de base de datos (usuarios, productos, categorías, pedidos, inventario)
- [ ] Endpoint GET /api/productos funcionando con datos reales

### Sprint 2 — 18 de septiembre al 2 de octubre
**Objetivo:** API REST funcional + autenticación backend

- [ ] Endpoints CRUD de productos
- [ ] Endpoint POST /api/pedidos
- [ ] Reemplazar products.js mock por consumo real vía Axios
- [ ] Sistema de autenticación en Flask (JWT + hash de contraseñas)
- [ ] Endpoints POST /api/auth/registro y POST /api/auth/login

### Sprint 3 — 2 al 16 de octubre
**Objetivo:** Autenticación funcional en frontend + pedidos del cliente

- [ ] Formulario de Login/Registro conectado al backend real
- [ ] Manejo de sesión (token) y rutas protegidas en React Router
- [ ] Página "Mis pedidos" (historial + estado)
- [ ] Cerrar sesión funcional

### Sprint 4 — 16 al 30 de octubre
**Objetivo:** Panel administrativo — gestión operativa

- [ ] Layout del panel admin (rutas protegidas para rol administrador)
- [ ] CRUD visual de productos y categorías
- [ ] Gestión de inventario (stock, alertas de stock bajo)
- [ ] Gestión de pedidos (cambio de estados)

### Sprint 5 — 30 de octubre al 13 de noviembre
**Objetivo:** Reportes + integración Telegram

- [ ] Dashboard de ventas/estadísticas
- [ ] Bot de Telegram: notificaciones (nuevo pedido, stock bajo)
- [ ] Asistente conversacional básico (consultas simples al backend)

### Buffer final — 13 al 20 de noviembre
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
