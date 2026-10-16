-- Bucket para fotos públicas del catálogo. Las subidas pasan por Flask/ADMINISTRADOR.
BEGIN;
INSERT INTO storage.buckets(id, name, public, file_size_limit, allowed_mime_types)
VALUES ('productos', 'productos', TRUE, 5242880,
    ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO NOTHING;
-- No conceder INSERT/UPDATE/DELETE a anon o authenticated en storage.objects.
COMMIT;
