# Contexto del proyecto: Sistema Web para Pizzería

Proyecto de titulación — Ingeniería de Sistemas.
Prioridad: calidad académica y comprensión del código > velocidad de desarrollo.

## Stack fijo (NO sugerir alternativas sin que se pida explícitamente)
- Frontend: React 19 + Vite + JavaScript (JSX, sin TypeScript)
- Gestor de paquetes: pnpm (no npm ni yarn)
- UI: Bootstrap + React Bootstrap
- Routing: React Router (react-router-dom)
- HTTP: Axios
- Backend: Python + Flask
- Base de datos: PostgreSQL vía Supabase

## Reglas de arquitectura — NO sugerir:
- Next.js, Vue, Angular, Django, Firebase, MongoDB
- Tailwind, Material UI, Chakra UI u otras librerías de UI
- Redux, Zustand, MobX u otras librerías de estado global
- TypeScript (el proyecto usa JavaScript puro)

## Principios de código
- Evitar sobreingeniería: sin abstracciones, capas o patrones innecesarios.
- Preferir componentes funcionales simples de React (con hooks estándar:
  useState, useEffect, useContext).
- Seguridad SIEMPRE validada en el backend (Flask), nunca solo en frontend.
- No implementar funcionalidades no solicitadas (favoritos, cupones, perfil
  avanzado, etc.) salvo que se pida explícitamente.
- Priorizar código legible y comentado sobre código "clever" o comprimido.

## Estructura del frontend
frontend/src/
├── components/   → piezas reutilizables (Navbar, ProductCard, etc.)
├── pages/        → vistas completas (Home, Catalogo, Carrito, Login)
├── layouts/      → estructura común (MainLayout con Navbar + Outlet)

## Roles del sistema (para cuando se implemente auth)
- CLIENTE: ver catálogo, gestionar carrito, ver sus propios pedidos.
- ADMINISTRADOR: gestión de productos, inventario, pedidos, ventas, dashboard.

## Contexto académico
Este es un trabajo de titulación. El estudiante debe poder entender,
explicar y defender cada decisión técnica. Evitar generar código que
el estudiante no pueda justificar en una defensa oral.