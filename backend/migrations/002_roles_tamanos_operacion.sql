-- Aplicar después de 001. Conserva usuarios, productos e historial existentes.
BEGIN;
ALTER TABLE public.usuarios ADD COLUMN IF NOT EXISTS roles TEXT[];
UPDATE public.usuarios SET roles = ARRAY[rol] WHERE roles IS NULL;
ALTER TABLE public.usuarios ALTER COLUMN roles SET DEFAULT ARRAY['CLIENTE']::TEXT[];
ALTER TABLE public.usuarios ALTER COLUMN roles SET NOT NULL;
ALTER TABLE public.usuarios ADD CONSTRAINT usuarios_roles_validos CHECK (
    cardinality(roles) BETWEEN 1 AND 3
    AND roles <@ ARRAY['CLIENTE','VENDEDOR','ADMINISTRADOR']::TEXT[]
    AND array_position(roles, NULL) IS NULL
);
-- rol queda como dato heredado; el código nuevo solo autoriza con roles.
ALTER TABLE public.productos ADD COLUMN IF NOT EXISTS tamano VARCHAR(40);
-- NULL en pedidos anteriores: no se puede asumir si descontaron inventario.
ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS stock_descontado BOOLEAN;
ALTER TABLE public.detalle_pedidos ADD COLUMN IF NOT EXISTS nombre_producto TEXT;
ALTER TABLE public.detalle_pedidos ADD COLUMN IF NOT EXISTS tamano TEXT;
UPDATE public.detalle_pedidos d SET nombre_producto = p.nombre, tamano = p.tamano
FROM public.productos p WHERE p.id = d.producto_id AND d.nombre_producto IS NULL;

CREATE TABLE public.ventas (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL UNIQUE REFERENCES public.pedidos(id),
    vendedor_id INTEGER REFERENCES public.usuarios(id) ON DELETE SET NULL,
    fecha_venta TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(10,2) NOT NULL CHECK(total >= 0),
    metodo_pago TEXT NOT NULL CHECK(metodo_pago IN ('EFECTIVO','QR','TARJETA'))
);
CREATE TABLE public.historial_estados (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES public.pedidos(id),
    usuario_id INTEGER REFERENCES public.usuarios(id) ON DELETE SET NULL,
    estado_anterior TEXT NOT NULL,
    estado_nuevo TEXT NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX pedidos_usuario_fecha ON public.pedidos(usuario_id, fecha_pedido DESC);
CREATE INDEX ventas_fecha ON public.ventas(fecha_venta);
ALTER TABLE public.usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.productos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventario ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pedidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.detalle_pedidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.historial_estados ENABLE ROW LEVEL SECURITY;
-- Todo acceso de la aplicación pasa por Flask y su clave secreta.
REVOKE ALL ON public.usuarios, public.productos, public.categorias, public.inventario,
    public.pedidos, public.detalle_pedidos, public.ventas, public.historial_estados
    FROM anon, authenticated;
GRANT ALL ON public.usuarios, public.productos, public.categorias, public.inventario,
    public.pedidos, public.detalle_pedidos, public.ventas, public.historial_estados TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.ventas_id_seq, public.historial_estados_id_seq TO service_role;

CREATE OR REPLACE FUNCTION public.guardar_tamano_y_nombre_detalle()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path=public AS $$
BEGIN
    SELECT nombre, tamano INTO NEW.nombre_producto, NEW.tamano
    FROM public.productos WHERE id = NEW.producto_id;
    RETURN NEW;
END;
$$;
CREATE TRIGGER detalle_snapshot BEFORE INSERT ON public.detalle_pedidos
FOR EACH ROW EXECUTE FUNCTION public.guardar_tamano_y_nombre_detalle();

CREATE OR REPLACE FUNCTION public.crear_producto_con_inventario(p_producto JSONB, p_stock_inicial INTEGER)
RETURNS JSONB LANGUAGE plpgsql SECURITY INVOKER SET search_path=public AS $$
DECLARE v_producto public.productos%ROWTYPE;
BEGIN
    IF p_stock_inicial IS NULL OR p_stock_inicial < 0 THEN
        RAISE EXCEPTION 'El stock inicial debe ser un entero no negativo.';
    END IF;
    INSERT INTO public.productos(nombre,descripcion,precio,categoria_id,imagen,activo,tamano)
    VALUES(p_producto->>'nombre',p_producto->>'descripcion',(p_producto->>'precio')::NUMERIC,
        (p_producto->>'categoria_id')::INTEGER,p_producto->>'imagen',TRUE,NULLIF(p_producto->>'tamano',''))
    RETURNING * INTO v_producto;
    INSERT INTO public.inventario(producto_id,stock_actual,stock_minimo)
    VALUES(v_producto.id,p_stock_inicial,10);
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

    INSERT INTO public.pedidos (usuario_id, total, direccion_entrega, telefono_contacto, metodo_pago, stock_descontado)
    VALUES (p_usuario_id, 0, btrim(p_direccion_entrega), p_telefono_contacto, p_metodo_pago, TRUE)
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

CREATE OR REPLACE FUNCTION public.cambiar_roles(p_actor INTEGER,p_usuario INTEGER,p_roles TEXT[])
RETURNS JSONB LANGUAGE plpgsql SECURITY INVOKER SET search_path=public AS $$
DECLARE v_usuario public.usuarios%ROWTYPE;
BEGIN
    LOCK TABLE public.usuarios IN SHARE ROW EXCLUSIVE MODE;
    IF NOT EXISTS(SELECT 1 FROM public.usuarios WHERE id=p_actor AND 'ADMINISTRADOR'=ANY(roles)) THEN
        RAISE EXCEPTION 'Solo un administrador puede asignar roles.';
    END IF;
    IF p_roles IS NULL OR cardinality(p_roles) NOT BETWEEN 1 AND 3
       OR NOT p_roles <@ ARRAY['CLIENTE','VENDEDOR','ADMINISTRADOR']::TEXT[]
       OR array_position(p_roles,NULL) IS NOT NULL THEN
        RAISE EXCEPTION 'Seleccione al menos un rol válido.';
    END IF;
    SELECT * INTO v_usuario FROM public.usuarios WHERE id=p_usuario;
    IF NOT FOUND THEN RAISE EXCEPTION 'Usuario no encontrado.'; END IF;
    IF 'ADMINISTRADOR'=ANY(v_usuario.roles) AND NOT 'ADMINISTRADOR'=ANY(p_roles)
       AND (SELECT count(*) FROM public.usuarios WHERE 'ADMINISTRADOR'=ANY(roles))=1 THEN
        RAISE EXCEPTION 'No se puede quitar al último administrador.';
    END IF;
    UPDATE public.usuarios SET roles=ARRAY(SELECT DISTINCT unnest(p_roles) ORDER BY 1) WHERE id=p_usuario
    RETURNING * INTO v_usuario;
    RETURN to_jsonb(v_usuario)-'password_hash'-'rol';
END;
$$;

CREATE OR REPLACE FUNCTION public.cambiar_estado_pedido(p_actor INTEGER,p_pedido INTEGER,p_estado TEXT)
RETURNS JSONB LANGUAGE plpgsql SECURITY INVOKER SET search_path=public AS $$
DECLARE v_pedido public.pedidos%ROWTYPE; v_linea RECORD;
BEGIN
    IF NOT EXISTS(SELECT 1 FROM public.usuarios WHERE id=p_actor
        AND roles && ARRAY['ADMINISTRADOR','VENDEDOR']::TEXT[]) THEN
        RAISE EXCEPTION 'No tiene permisos para gestionar pedidos.';
    END IF;
    SELECT * INTO v_pedido FROM public.pedidos WHERE id=p_pedido FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Pedido no encontrado.'; END IF;
    IF v_pedido.estado=p_estado THEN RETURN to_jsonb(v_pedido); END IF;
    IF NOT ((v_pedido.estado='PENDIENTE' AND p_estado IN ('EN_PREPARACION','CANCELADO'))
        OR (v_pedido.estado='EN_PREPARACION' AND p_estado IN ('EN_CAMINO','CANCELADO'))
        OR (v_pedido.estado='EN_CAMINO' AND p_estado IN ('ENTREGADO','CANCELADO'))) THEN
        RAISE EXCEPTION 'La transición de estado no está permitida.';
    END IF;
    IF p_estado='CANCELADO' AND v_pedido.stock_descontado IS NULL THEN
        RAISE EXCEPTION 'Pedido anterior a la migración: revise si descontó stock antes de cancelar.';
    END IF;
    IF p_estado='CANCELADO' AND v_pedido.stock_descontado THEN
        FOR v_linea IN SELECT producto_id,sum(cantidad) AS cantidad FROM public.detalle_pedidos
            WHERE pedido_id=p_pedido AND producto_id IS NOT NULL GROUP BY producto_id ORDER BY producto_id
        LOOP
            UPDATE public.inventario SET stock_actual=stock_actual+v_linea.cantidad,
                actualizado_en=CURRENT_TIMESTAMP WHERE producto_id=v_linea.producto_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'No se pudo devolver el stock.'; END IF;
        END LOOP;
    END IF;
    INSERT INTO public.historial_estados(pedido_id,usuario_id,estado_anterior,estado_nuevo)
    VALUES(p_pedido,p_actor,v_pedido.estado,p_estado);
    UPDATE public.pedidos SET estado=p_estado,
        stock_descontado=CASE WHEN p_estado='CANCELADO' THEN FALSE ELSE stock_descontado END
        WHERE id=p_pedido RETURNING * INTO v_pedido;
    RETURN to_jsonb(v_pedido);
END;
$$;

CREATE OR REPLACE FUNCTION public.registrar_venta(p_actor INTEGER,p_pedido INTEGER,p_metodo TEXT)
RETURNS JSONB LANGUAGE plpgsql SECURITY INVOKER SET search_path=public AS $$
DECLARE v_pedido public.pedidos%ROWTYPE; v_venta public.ventas%ROWTYPE;
BEGIN
    IF NOT EXISTS(SELECT 1 FROM public.usuarios WHERE id=p_actor
        AND roles && ARRAY['ADMINISTRADOR','VENDEDOR']::TEXT[]) THEN
        RAISE EXCEPTION 'No tiene permisos para registrar ventas.';
    END IF;
    IF p_metodo IS NULL OR p_metodo NOT IN ('EFECTIVO','QR','TARJETA') THEN
        RAISE EXCEPTION 'Método de pago inválido.';
    END IF;
    SELECT * INTO v_pedido FROM public.pedidos WHERE id=p_pedido FOR UPDATE;
    IF NOT FOUND OR v_pedido.estado<>'ENTREGADO' THEN
        RAISE EXCEPTION 'Solo se puede cobrar un pedido entregado.';
    END IF;
    IF EXISTS(SELECT 1 FROM public.ventas WHERE pedido_id=p_pedido) THEN
        RAISE EXCEPTION 'La venta ya fue registrada.';
    END IF;
    INSERT INTO public.ventas(pedido_id,vendedor_id,total,metodo_pago)
    VALUES(p_pedido,p_actor,v_pedido.total,p_metodo) RETURNING * INTO v_venta;
    UPDATE public.pedidos SET metodo_pago=p_metodo WHERE id=p_pedido;
    RETURN to_jsonb(v_venta);
END;
$$;

CREATE OR REPLACE FUNCTION public.venta_directa(p_actor INTEGER,p_items JSONB,p_metodo TEXT)
RETURNS JSONB LANGUAGE plpgsql SECURITY INVOKER SET search_path=public AS $$
DECLARE v_resultado JSONB; v_pedido INTEGER; v_venta JSONB;
BEGIN
    IF NOT EXISTS(SELECT 1 FROM public.usuarios WHERE id=p_actor
        AND roles && ARRAY['ADMINISTRADOR','VENDEDOR']::TEXT[]) THEN
        RAISE EXCEPTION 'No tiene permisos para registrar ventas.';
    END IF;
    v_resultado:=public.crear_pedido_atomico(p_actor,'Venta en local',NULL,p_metodo,p_items);
    v_pedido:=(v_resultado->'pedido'->>'id')::INTEGER;
    UPDATE public.pedidos SET estado='ENTREGADO' WHERE id=v_pedido;
    INSERT INTO public.historial_estados(pedido_id,usuario_id,estado_anterior,estado_nuevo)
    VALUES(v_pedido,p_actor,'PENDIENTE','ENTREGADO');
    v_venta:=public.registrar_venta(p_actor,v_pedido,p_metodo);
    RETURN jsonb_build_object('pedido_id',v_pedido,'venta',v_venta);
END;
$$;

CREATE OR REPLACE FUNCTION public.ajustar_inventario(
    p_producto INTEGER,p_stock INTEGER,p_minimo INTEGER,p_esperado INTEGER)
RETURNS JSONB LANGUAGE plpgsql SECURITY INVOKER SET search_path=public AS $$
DECLARE v_inventario public.inventario%ROWTYPE;
BEGIN
    IF p_stock IS NULL OR p_minimo IS NULL OR p_stock<0 OR p_minimo<0 THEN
        RAISE EXCEPTION 'Stock y mínimo deben ser no negativos.';
    END IF;
    SELECT * INTO v_inventario FROM public.inventario WHERE producto_id=p_producto FOR UPDATE;
    IF FOUND THEN
        IF p_esperado IS DISTINCT FROM v_inventario.stock_actual THEN
            RAISE EXCEPTION 'El stock cambió. Recargue antes de guardar.';
        END IF;
        UPDATE public.inventario SET stock_actual=p_stock,stock_minimo=p_minimo,
            actualizado_en=CURRENT_TIMESTAMP WHERE producto_id=p_producto RETURNING * INTO v_inventario;
    ELSE
        IF p_esperado IS NOT NULL THEN RAISE EXCEPTION 'Recargue el inventario.'; END IF;
        INSERT INTO public.inventario(producto_id,stock_actual,stock_minimo)
        VALUES(p_producto,p_stock,p_minimo) RETURNING * INTO v_inventario;
    END IF;
    RETURN to_jsonb(v_inventario);
END;
$$;

CREATE OR REPLACE FUNCTION public.reporte_ventas(p_desde TIMESTAMPTZ,p_hasta TIMESTAMPTZ)
RETURNS JSONB LANGUAGE sql SECURITY INVOKER SET search_path=public AS $$
    SELECT jsonb_build_object(
        'total',COALESCE((SELECT sum(total) FROM public.ventas WHERE fecha_venta>=p_desde AND fecha_venta<p_hasta),0),
        'cantidad', (SELECT count(*) FROM public.ventas WHERE fecha_venta>=p_desde AND fecha_venta<p_hasta),
        'por_pago',COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (
            SELECT metodo_pago,count(*) AS cantidad,sum(total) AS total FROM public.ventas
            WHERE fecha_venta>=p_desde AND fecha_venta<p_hasta GROUP BY metodo_pago ORDER BY metodo_pago)t),'[]'::JSONB),
        'por_dia',COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (
            SELECT (fecha_venta AT TIME ZONE 'America/La_Paz')::DATE AS fecha,count(*) AS cantidad,sum(total) AS total
            FROM public.ventas WHERE fecha_venta>=p_desde AND fecha_venta<p_hasta GROUP BY 1 ORDER BY 1)t),'[]'::JSONB),
        'por_producto',COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (
            SELECT d.nombre_producto AS nombre,d.tamano,sum(d.cantidad) AS cantidad,sum(d.subtotal) AS total
            FROM public.ventas v JOIN public.detalle_pedidos d ON d.pedido_id=v.pedido_id
            WHERE v.fecha_venta>=p_desde AND v.fecha_venta<p_hasta GROUP BY d.nombre_producto,d.tamano
            ORDER BY sum(d.cantidad) DESC LIMIT 50)t),'[]'::JSONB),
        'consumo',COALESCE((SELECT jsonb_agg(to_jsonb(t)) FROM (
            SELECT d.nombre_producto AS nombre,d.tamano,sum(d.cantidad) AS cantidad
            FROM public.pedidos p JOIN public.detalle_pedidos d ON d.pedido_id=p.id
            WHERE p.fecha_pedido>=p_desde AND p.fecha_pedido<p_hasta AND p.estado<>'CANCELADO'
            GROUP BY d.nombre_producto,d.tamano ORDER BY sum(d.cantidad) DESC LIMIT 50)t),'[]'::JSONB)
    );
$$;

REVOKE ALL ON FUNCTION public.cambiar_roles(INTEGER,INTEGER,TEXT[]),
 public.cambiar_estado_pedido(INTEGER,INTEGER,TEXT),public.registrar_venta(INTEGER,INTEGER,TEXT),
 public.venta_directa(INTEGER,JSONB,TEXT),public.ajustar_inventario(INTEGER,INTEGER,INTEGER,INTEGER),
 public.reporte_ventas(TIMESTAMPTZ,TIMESTAMPTZ),public.guardar_tamano_y_nombre_detalle()
 FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.cambiar_roles(INTEGER,INTEGER,TEXT[]),
 public.cambiar_estado_pedido(INTEGER,INTEGER,TEXT),public.registrar_venta(INTEGER,INTEGER,TEXT),
 public.venta_directa(INTEGER,JSONB,TEXT),public.ajustar_inventario(INTEGER,INTEGER,INTEGER,INTEGER),
 public.reporte_ventas(TIMESTAMPTZ,TIMESTAMPTZ),public.guardar_tamano_y_nombre_detalle()
 TO service_role;
COMMIT;
