-- Solo para PostgreSQL efímero. Supabase ya proporciona estos esquemas.
CREATE SCHEMA auth;
CREATE TABLE auth.users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    encrypted_password TEXT,
    raw_app_meta_data JSONB DEFAULT '{}'::JSONB,
    raw_user_meta_data JSONB DEFAULT '{}'::JSONB
);
CREATE SCHEMA storage;
CREATE TABLE storage.buckets (
    id TEXT PRIMARY KEY, name TEXT, public BOOLEAN,
    file_size_limit BIGINT, allowed_mime_types TEXT[]
);
GRANT USAGE ON SCHEMA auth TO service_role;
GRANT ALL ON auth.users TO service_role;
