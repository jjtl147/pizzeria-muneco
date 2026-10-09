-- Ejecutar en una base de PRUEBAS con schema.sql y la migración instalados.
-- Se revierten los datos al final; las secuencias pueden avanzar.
BEGIN;
DO $$
DECLARE
    v_usuario INTEGER;
    v_producto INTEGER;
    v_inactivo INTEGER;
    v_resultado JSONB;
    v_stock INTEGER;
    v_pedidos BIGINT;
    v_detalles BIGINT;
    v_productos BIGINT;
    v_fallo BOOLEAN;
BEGIN
    INSERT INTO public.usuarios (nombre, email, password_hash)
    VALUES ('Prueba transaccional', 'prueba-' || txid_current() || '@example.test', 'solo-prueba')
    RETURNING id INTO v_usuario;

    v_resultado := public.crear_producto_con_inventario(
        '{"nombre":"Pizza de prueba","precio":10.25}', 5);
    v_producto := (v_resultado->>'id')::INTEGER;
    IF NOT EXISTS (SELECT 1 FROM public.inventario WHERE producto_id = v_producto AND stock_actual = 5) THEN
        RAISE EXCEPTION 'Fallo: producto sin inventario.';
    END IF;

    -- Ítems repetidos deben sumar cantidades y usar el precio real.
    v_resultado := public.crear_pedido_atomico(v_usuario, 'Dirección de prueba', NULL, 'EFECTIVO',
        jsonb_build_array(
            jsonb_build_object('producto_id', v_producto, 'cantidad', 1, 'precio', 0),
            jsonb_build_object('producto_id', v_producto, 'cantidad', 2)));
    SELECT stock_actual INTO v_stock FROM public.inventario WHERE producto_id = v_producto;
    IF v_stock <> 2 OR (v_resultado->'pedido'->>'total')::NUMERIC <> 30.75
       OR jsonb_array_length(v_resultado->'detalles') <> 1 THEN
        RAISE EXCEPTION 'Fallo: total, agrupación o descuento de stock incorrecto.';
    END IF;

    v_resultado := public.crear_producto_con_inventario('{"nombre":"Producto desactivado","precio":5}', 10);
    v_inactivo := (v_resultado->>'id')::INTEGER;
    UPDATE public.productos SET activo = FALSE WHERE id = v_inactivo;
    SELECT count(*) INTO v_pedidos FROM public.pedidos;
    SELECT count(*) INTO v_detalles FROM public.detalle_pedidos;

    -- El primer ítem escribe detalles y descuenta stock; el segundo debe
    -- provocar rollback de todo el pedido, incluyendo ese primer descuento.
    v_fallo := FALSE;
    BEGIN
        PERFORM public.crear_pedido_atomico(v_usuario, 'Dirección', NULL, 'EFECTIVO',
            jsonb_build_array(
                jsonb_build_object('producto_id', v_producto, 'cantidad', 1),
                jsonb_build_object('producto_id', v_inactivo, 'cantidad', 1)));
    EXCEPTION WHEN SQLSTATE 'P0001' THEN
        v_fallo := TRUE;
    END;
    IF NOT v_fallo OR (SELECT count(*) FROM public.pedidos) <> v_pedidos
       OR (SELECT count(*) FROM public.detalle_pedidos) <> v_detalles
       OR (SELECT stock_actual FROM public.inventario WHERE producto_id = v_producto) <> 2 THEN
        RAISE EXCEPTION 'Fallo: el pedido incompleto no se revirtió.';
    END IF;

    v_fallo := FALSE;
    BEGIN
        PERFORM public.crear_pedido_atomico(v_usuario, 'Dirección', NULL, 'EFECTIVO',
            jsonb_build_array(jsonb_build_object('producto_id', v_producto, 'cantidad', 3)));
    EXCEPTION WHEN SQLSTATE 'P0001' THEN
        v_fallo := TRUE;
    END;
    IF NOT v_fallo OR (SELECT count(*) FROM public.pedidos) <> v_pedidos
       OR (SELECT stock_actual FROM public.inventario WHERE producto_id = v_producto) <> 2 THEN
        RAISE EXCEPTION 'Fallo: se aceptó un pedido sin stock suficiente.';
    END IF;

    -- También se debe revertir un producto si no puede crearse su inventario.
    SELECT count(*) INTO v_productos FROM public.productos;
    v_fallo := FALSE;
    BEGIN
        PERFORM public.crear_producto_con_inventario('{"nombre":"Stock negativo","precio":5}', -1);
    EXCEPTION WHEN SQLSTATE 'P0001' THEN
        v_fallo := TRUE;
    END;
    IF NOT v_fallo OR (SELECT count(*) FROM public.productos) <> v_productos THEN
        RAISE EXCEPTION 'Fallo: se aceptó stock inicial negativo.';
    END IF;

    IF has_function_privilege('anon', 'public.crear_pedido_atomico(integer,text,text,text,jsonb)', 'EXECUTE')
       OR has_function_privilege('authenticated', 'public.crear_pedido_atomico(integer,text,text,text,jsonb)', 'EXECUTE') THEN
        RAISE EXCEPTION 'Fallo: la función de pedidos permite acceso público.';
    END IF;
    RAISE NOTICE 'Pruebas de operaciones atómicas correctas.';
END;
$$;
ROLLBACK;
