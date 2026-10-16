-- Aplicar después de 004. El permiso vigente siempre está en usuarios.roles.
-- No elimina cuentas, contraseñas heredadas, pedidos, ventas ni tablas.
BEGIN;
SET LOCAL lock_timeout = '5s';

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.usuarios
        WHERE roles IS NULL OR cardinality(roles) NOT BETWEEN 1 AND 3
            OR NOT roles <@ ARRAY['CLIENTE','VENDEDOR','ADMINISTRADOR']::TEXT[]
            OR array_position(roles, NULL) IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'Hay perfiles con roles inválidos; revisar antes de retirar rol.';
    END IF;
END;
$$;

-- Sin CASCADE: si hay dependencias ajenas al proyecto, la transacción falla
-- en lugar de borrarlas. DROP COLUMN retira también su CHECK/default antiguos.
ALTER TABLE public.usuarios DROP COLUMN IF EXISTS rol;
COMMENT ON COLUMN public.usuarios.roles IS
    'Permisos vigentes de la aplicación: CLIENTE, VENDEDOR y ADMINISTRADOR combinables.';

COMMIT;

-- Comprobación para el SQL Editor: rol debe ser FALSE y roles TRUE.
SELECT
    EXISTS(SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='usuarios' AND column_name='rol') AS rol_antiguo_existe,
    EXISTS(SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='usuarios' AND column_name='roles') AS roles_vigentes_existen;
