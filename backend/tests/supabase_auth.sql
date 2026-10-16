-- Ejecutar solo en base de pruebas con un esquema auth aislado.
BEGIN;
DO $$
DECLARE antiguo INTEGER; cantidad INTEGER; fallo BOOLEAN;
BEGIN
    INSERT INTO public.usuarios(nombre,email,password_hash,roles)
    VALUES('Admin heredado','heredado@auth.test','hash',ARRAY['ADMINISTRADOR']) RETURNING id INTO antiguo;
    INSERT INTO public.pedidos(usuario_id,total,direccion_entrega)
    VALUES(antiguo,0,'Pedido histórico');
    -- user_metadata no puede reclamar un ID ni asignar roles.
    INSERT INTO auth.users(id,email,raw_user_meta_data) VALUES(
        '00000000-0000-0000-0000-000000000001','nuevo@auth.test',
        jsonb_build_object('nombre','Nuevo','roles',ARRAY['ADMINISTRADOR'],'legacy_usuario_id',antiguo));
    IF (SELECT roles FROM public.usuarios WHERE email='nuevo@auth.test') <> ARRAY['CLIENTE'] THEN
        RAISE EXCEPTION 'Registro público escaló permisos';
    END IF;
    fallo:=FALSE;
    BEGIN
        INSERT INTO auth.users(id,email) VALUES('00000000-0000-0000-0000-000000000002','HEREDADO@auth.test');
    EXCEPTION WHEN unique_violation THEN fallo:=TRUE; END;
    IF NOT fallo THEN RAISE EXCEPTION 'Se reclamó una cuenta por correo'; END IF;
    -- Importación autorizada por metadatos administrativos, preservando ID.
    INSERT INTO auth.users(id,email,raw_app_meta_data) VALUES(
        '00000000-0000-0000-0000-000000000003','heredado@auth.test',
        jsonb_build_object('legacy_usuario_id',antiguo));
    IF NOT EXISTS(SELECT 1 FROM public.usuarios WHERE id=antiguo
        AND auth_user_id='00000000-0000-0000-0000-000000000003'
        AND password_hash IS NULL AND roles=ARRAY['ADMINISTRADOR']) THEN
        RAISE EXCEPTION 'Se perdieron ID, roles o no se eliminó el hash';
    END IF;
    IF NOT EXISTS(SELECT 1 FROM public.pedidos WHERE usuario_id=antiguo) THEN
        RAISE EXCEPTION 'Se perdió el historial';
    END IF;
    fallo:=FALSE;
    BEGIN
        INSERT INTO auth.users(id,email,raw_app_meta_data) VALUES(
            '00000000-0000-0000-0000-000000000004','otro@auth.test',
            jsonb_build_object('legacy_usuario_id',antiguo));
    EXCEPTION WHEN SQLSTATE 'P0001' THEN fallo:=TRUE; END;
    IF NOT fallo THEN RAISE EXCEPTION 'Se permitió una vinculación inválida'; END IF;
    DELETE FROM auth.users WHERE id='00000000-0000-0000-0000-000000000003';
    IF NOT EXISTS(SELECT 1 FROM public.usuarios WHERE id=antiguo AND auth_user_id IS NULL AND password_hash IS NULL) THEN
        RAISE EXCEPTION 'Borrar Auth eliminó el perfil o restauró credenciales heredadas';
    END IF;
    IF NOT EXISTS(SELECT 1 FROM storage.buckets WHERE id='productos' AND public AND file_size_limit=5242880) THEN
        RAISE EXCEPTION 'Bucket de imágenes sin configurar';
    END IF;
END;
$$;
ROLLBACK;
