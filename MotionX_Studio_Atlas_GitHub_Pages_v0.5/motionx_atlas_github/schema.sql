-- MotionX Studio Atlas — PostgreSQL 16 + PostGIS foundation
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE studios (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), canonical_name text NOT NULL, legal_name text, website text, registration_number text, registration_jurisdiction text, operating_status text NOT NULL DEFAULT 'unverified' CHECK (operating_status IN ('active','unverified','closed','merged')), parent_studio_id uuid REFERENCES studios(id), created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE studio_locations (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), studio_id uuid NOT NULL REFERENCES studios(id) ON DELETE CASCADE, label text, street_address text, city text NOT NULL, region text, country_code char(2) NOT NULL, location geography(Point,4326), coordinate_precision text NOT NULL DEFAULT 'approximate' CHECK (coordinate_precision IN ('exact','street','city','approximate')), public_email text, public_phone text, is_public boolean NOT NULL DEFAULT true);
CREATE INDEX studio_locations_geo_idx ON studio_locations USING gist(location);
CREATE TABLE categories (id serial PRIMARY KEY, slug text UNIQUE NOT NULL, label text NOT NULL);
CREATE TABLE studio_categories (studio_id uuid REFERENCES studios(id) ON DELETE CASCADE, category_id integer REFERENCES categories(id), PRIMARY KEY(studio_id,category_id));
CREATE TABLE capabilities (id serial PRIMARY KEY, slug text UNIQUE NOT NULL, label text NOT NULL);
CREATE TABLE sources (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), url text NOT NULL, publisher text, source_type text, license_notes text, accessed_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE studio_capabilities (studio_id uuid REFERENCES studios(id) ON DELETE CASCADE, capability_id integer REFERENCES capabilities(id), evidence_state text NOT NULL CHECK (evidence_state IN ('confirmed','likely','unknown')), source_id uuid REFERENCES sources(id), checked_at timestamptz, PRIMARY KEY(studio_id,capability_id));
CREATE TABLE verification_events (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), studio_id uuid REFERENCES studios(id) ON DELETE CASCADE, source_id uuid REFERENCES sources(id), field_name text NOT NULL, old_value text, new_value text, reviewer_id uuid, checked_at timestamptz NOT NULL DEFAULT now());
-- Private schema: never expose through public API or unauthenticated database role.
CREATE SCHEMA motionx_private;
CREATE TABLE motionx_private.leads (studio_id uuid PRIMARY KEY REFERENCES public.studios(id) ON DELETE CASCADE, score integer CHECK (score BETWEEN 0 AND 100), stage text NOT NULL DEFAULT 'research', owner_user_id uuid, notes text, next_followup_at timestamptz, updated_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE motionx_private.interactions (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), studio_id uuid REFERENCES public.studios(id) ON DELETE CASCADE, owner_user_id uuid NOT NULL, channel text, summary text NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now());
REVOKE ALL ON SCHEMA motionx_private FROM PUBLIC;
-- Production deployment must explicitly configure roles, RLS, auth, and grants.
