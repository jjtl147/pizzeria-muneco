-- Ejecutar después de 002 en el SQL Editor de Supabase.
-- No borra usuarios ni modifica los IDs de pedidos/ventas.
BEGIN;
ALTER TABLE public.usuarios ADD COLUMN auth_user_id UUID UNIQUE
    REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE public.usuarios ALTER COLUMN password_hash DROP NOT NULL;
CREATE UNIQUE INDEX usuarios_email_normalizado ON public.usuarios(lower(email));

CREATE FUNCTION public.crear_perfil_auth()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
    v_legacy TEXT := NEW.raw_app_meta_data->>'legacy_usuario_id';
    v_id INTEGER;
BEGIN
    IF NEW.email IS NULL THEN
        RAISE EXCEPTION 'Se requiere un correo para crear el perfil.';
    END IF;
    IF v_legacy IS NOT NULL THEN
        -- app_metadata solo se escribe con la API administrativa.
        UPDATE public.usuarios
        SET auth_user_id = NEW.id, password_hash = NULL
        WHERE id = v_legacy::INTEGER AND lower(email) = lower(NEW.email)
            AND auth_user_id IS NULL AND password_hash IS NOT NULL
        RETURNING id INTO v_id;
        IF v_id IS NULL THEN
            RAISE EXCEPTION 'No se pudo vincular la identidad heredada.';
        END IF;
    ELSE
        -- Nunca unir por correo ni confiar en roles de user_metadata.
        -- Si existe el correo heredado, la unicidad bloquea el registro:
        -- debe migrarse acreditando la contraseña anterior en Flask.
        INSERT INTO public.usuarios(auth_user_id, nombre, email, roles, telefono, direccion)
        VALUES(NEW.id,
            COALESCE(NULLIF(left(trim(NEW.raw_user_meta_data->>'nombre'), 100), ''), 'Cliente'),
            lower(NEW.email), ARRAY['CLIENTE']::TEXT[],
            left(NEW.raw_user_meta_data->>'telefono', 20),
            left(NEW.raw_user_meta_data->>'direccion', 1000));
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION public.crear_perfil_auth() FROM PUBLIC, anon, authenticated;
CREATE TRIGGER crear_perfil_tras_registro
AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.crear_perfil_auth();
COMMENT ON COLUMN public.usuarios.password_hash IS
    'Solo para migrar cuentas heredadas al primer login; NULL tras vincular Supabase Auth.';
COMMIT;
