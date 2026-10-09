-- Ejecutar en el SQL Editor de Supabase después de schema.sql.
-- Estas funciones son exclusivas del backend (clave service_role).
BEGIN;

CREATE OR REPLACE FUNCTION public.crear_producto_con_inventario(
    p_producto JSONB, p_stock_inicial INTEGER
) RETURNS JSONB
LANGUAGE plpgsql SECURITY INVOKER SET search_path = public
AS $$
DECLARE
    v_producto public.productos%ROWTYPE;
BEGIN
    IF p_stock_inicial IS NULL OR p_stock_inicial < 0 THEN
        RAISE EXCEPTION 'El stock inicial debe ser un entero no negativo.';
    END IF;
    INSERT INTO public.productos (nombre, descripcion, precio, categoria_id, imagen, activo)
    VALUES (p_producto->>'nombre', p_producto->>'descripcion',
            (p_producto->>'precio')::NUMERIC, (p_producto->>'categoria_id')::INTEGER,
            p_producto->>'imagen', TRUE)
    RETURNING * INTO v_producto;

    INSERT INTO public.inventario (producto_id, stock_actual, stock_minimo)
    VALUES (v_producto.id, p_stock_inicial, 10);
    RETURN to_jsonb(v_producto);
END;
$$;

CREATE OR REPLACE FUNCTION public.crear_pedido_atomico(
    p_usuario_id INTEGER, p_direccion_entrega TEXT, p_telefono_contacto TEXT,
    p_metodo_pago TEXT, p_items JSONB
) RETURNS JSONB
LANGUAGE plpgsql SECURITY INVOKER SET search_path = public
AS $$
DECLARE
    v_item JSONB;
    v_linea RECORD;
    v_producto public.productos%ROWTYPE;
    v_stock INTEGER;
    v_pedido public.pedidos%ROWTYPE;
    v_detalle public.detalle_pedidos%ROWTYPE;
    v_detalles JSONB := '[]'::JSONB;
    v_total NUMERIC(10, 2) := 0;
BEGIN
    IF p_usuario_id IS NULL OR NOT EXISTS (
        SELECT 1 FROM public.usuarios WHERE id = p_usuario_id
    ) THEN
        RAISE EXCEPTION 'Usuario no encontrado.';
    END IF;
    IF p_direccion_entrega IS NULL OR btrim(p_direccion_entrega) = ''
       OR p_metodo_pago IS NULL OR btrim(p_metodo_pago) = '' THEN
        RAISE EXCEPTION 'La dirección y el método de pago son obligatorios.';
    END IF;
    IF p_items IS NULL OR jsonb_typeof(p_items) <> 'array' THEN
        RAISE EXCEPTION 'Los ítems deben ser una lista.';
    END IF;
    IF jsonb_array_length(p_items) = 0 THEN
        RAISE EXCEPTION 'El pedido debe contener al menos un producto.';
    END IF;
    -- Validar también en PostgreSQL antes de realizar conversiones o escrituras.
    FOR v_item IN SELECT value FROM jsonb_array_elements(p_items) LOOP
        IF jsonb_typeof(v_item) <> 'object'
           OR jsonb_typeof(v_item->'producto_id') IS DISTINCT FROM 'number'
           OR jsonb_typeof(v_item->'cantidad') IS DISTINCT FROM 'number'
           OR (v_item->>'producto_id') !~ '^[1-9][0-9]*$'
           OR (v_item->>'cantidad') !~ '^[1-9][0-9]*$' THEN
            RAISE EXCEPTION 'Cada ítem requiere producto_id y cantidad enteros positivos.';
        END IF;
        IF (v_item->>'producto_id')::NUMERIC > 2147483647
           OR (v_item->>'cantidad')::NUMERIC > 2147483647 THEN
            RAISE EXCEPTION 'El ID o la cantidad supera el máximo permitido.';
        END IF;
    END LOOP;

    INSERT INTO public.pedidos (usuario_id, total, direccion_entrega, telefono_contacto, metodo_pago)
    VALUES (p_usuario_id, 0, btrim(p_direccion_entrega), p_telefono_contacto, p_metodo_pago)
    RETURNING * INTO v_pedido;

    -- Agrupar productos repetidos y bloquear siempre en orden de ID.
    -- Los bloqueos duran hasta terminar la transacción y evitan sobreventa.
    FOR v_linea IN
        SELECT (value->>'producto_id')::INTEGER AS producto_id,
               sum((value->>'cantidad')::BIGINT) AS cantidad
        FROM jsonb_array_elements(p_items)
        GROUP BY (value->>'producto_id')::INTEGER
        ORDER BY producto_id
    LOOP
        IF v_linea.cantidad > 2147483647 THEN
            RAISE EXCEPTION 'La cantidad acumulada supera el máximo permitido.';
        END IF;
        SELECT * INTO v_producto FROM public.productos
        WHERE id = v_linea.producto_id FOR UPDATE;
        IF NOT FOUND OR v_producto.activo IS DISTINCT FROM TRUE THEN
            RAISE EXCEPTION 'El producto % no está disponible.', v_linea.producto_id;
        END IF;

        SELECT stock_actual INTO v_stock FROM public.inventario
        WHERE producto_id = v_linea.producto_id FOR UPDATE;
        IF NOT FOUND OR v_stock < v_linea.cantidad THEN
            RAISE EXCEPTION 'Stock insuficiente para el producto %.', v_linea.producto_id;
        END IF;

        INSERT INTO public.detalle_pedidos
            (pedido_id, producto_id, cantidad, precio_unitario, subtotal)
        VALUES (v_pedido.id, v_producto.id, v_linea.cantidad,
                v_producto.precio, v_producto.precio * v_linea.cantidad)
        RETURNING * INTO v_detalle;

        UPDATE public.inventario
        SET stock_actual = stock_actual - v_linea.cantidad, actualizado_en = CURRENT_TIMESTAMP
        WHERE producto_id = v_producto.id;
        v_total := v_total + v_detalle.subtotal;
        v_detalles := v_detalles || jsonb_build_array(to_jsonb(v_detalle));
    END LOOP;

    UPDATE public.pedidos SET total = v_total WHERE id = v_pedido.id
    RETURNING * INTO v_pedido;
    RETURN jsonb_build_object('pedido', to_jsonb(v_pedido), 'detalles', v_detalles);
    -- Cualquier excepción revierte pedido, detalles y stock automáticamente.
END;
$$;

REVOKE ALL ON FUNCTION public.crear_producto_con_inventario(JSONB, INTEGER)
FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.crear_pedido_atomico(INTEGER, TEXT, TEXT, TEXT, JSONB)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.crear_producto_con_inventario(JSONB, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION public.crear_pedido_atomico(INTEGER, TEXT, TEXT, TEXT, JSONB) TO service_role;

COMMIT;
