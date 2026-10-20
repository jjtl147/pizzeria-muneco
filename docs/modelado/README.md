# Modelado, arquitectura y datos — Pizzería Muñeco

Preparado el 20 de octubre de 2026 a partir del código y de `backend/schema.sql`
con las migraciones 001–005. Las figuras representan código disponible; no
acreditan por sí mismas pruebas en producción.

- **[Ver las figuras y el texto por apartados](MODELADO_SISTEMA.md)**.
- **[Consultar las 23 especificaciones de casos de uso](CASOS_DE_USO.md)**.
- **[Consultar el diccionario de datos](DICCIONARIO_DATOS.md)**.
- **[Abrir la galería de imágenes](galeria.html)**.

## Insertar en el documento

Cada figura tiene una fuente editable en `fuentes/*.puml`, una imagen vectorial
en `svg/*.svg` y una imagen en `png/*.png`. En LibreOffice Writer, usar
**Insertar → Imagen** y elegir el SVG para conservar nitidez, o el PNG como
alternativa. Clases y entidad-relación convienen en página horizontal. Ajustar
los números de figura al documento y añadir «Fuente: elaboración propia a partir
del sistema implementado». La galería HTML permite recorrer e imprimir las figuras.

## Alcance y decisiones

- CLIENTE, VENDEDOR y ADMINISTRADOR son roles combinables, sin herencia entre
  actores. Tener ADMINISTRADOR o VENDEDOR no concede automáticamente CLIENTE.
- Catálogo y carrito admiten visitantes. Confirmar el pedido e historial propio
  requieren CLIENTE. La creación del pedido web no incluye registrar el cobro.
- Cobrar exige ENTREGADO y ausencia de venta previa. La venta local crea pedido,
  detalles, entrega y cobro en una sola transacción. No hay pasarela bancaria.
- Cada tamaño es una fila distinta de productos, con precio y stock propios.
  El consumo implementado mide productos de pedidos no cancelados.
- Clases representa un modelo conceptual del dominio, sin afirmar que exista un
  ORM. El ER representa las claves y cardinalidades del DDL físico.
- No se presentan como implementados insumos, recetas, dos sabores, CAPTCHA o
  nota libre. No se incluyen casos de mesa o reserva retirados del alcance.
- CU-20 describe código de subida de imágenes; la prueba real sigue pendiente.
- Telegram y LLM figuran como integraciones opcionales pendientes; no se añaden
  al catálogo principal de casos de uso.
- El despliegue representa desarrollo local y Supabase remoto. No se inventa
  hosting, dominio o infraestructura de producción.
- No se modifican el ODT ni las tareas o casillas de planificación.

No se usan `include` o `extend` para expresar orden temporal. La relación entre
pedir, entregar y cobrar se explica en actividades, secuencias y precondiciones.
Las validaciones internas no necesitan convertirse en casos de uso separados.

## Regenerar imágenes

Fuentes PlantUML con motor Java Smetana, sin Graphviz. Generadas con PlantUML
1.2024.8 en modo sin interfaz gráfica. El JAR es una herramienta temporal y no
una dependencia de la pizzería. Desde la raíz, con un JAR disponible:

```bash
java -Djava.awt.headless=true -jar /ruta/plantuml.jar -checkonly docs/modelado/fuentes
java -Djava.awt.headless=true -jar /ruta/plantuml.jar -tsvg -o ../svg docs/modelado/fuentes
java -Djava.awt.headless=true -jar /ruta/plantuml.jar -tpng -o ../png docs/modelado/fuentes
```

Editar las fuentes `.puml` y regenerar. Las imágenes se abren sin extensiones.

## Evidencia del repositorio

| Contenido | Fuente |
|---|---|
| Casos de uso, permisos y rutas | `backend/app.py`, `frontend/src/App.jsx` y paneles React |
| Identidad y cuentas heredadas | `backend/auth_supabase.py`, migración 003 |
| Transacciones de pedidos, stock y ventas | migraciones 001 y 002 |
| Modelo físico vigente | `backend/schema.sql` y migraciones 001–005 |
| Fotos | `backend/app.py` y migración 004 |
| Comunicación y renovación de sesión | `frontend/src/services/api.js` |
| CSV y consumo | `frontend/src/pages/admin/Reportes.jsx` |
| Integraciones | `backend/integrations.py` |
| Validaciones externas y alcance pendiente | `PLANIFICACION_SCRUM.md` |
