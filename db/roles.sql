-- Roles for the radar database. Locally a superuser runs this; on Neon
-- `radar-db provision` creates the same roles through the migrator.
--
-- radar_migrator  owns the schema and runs migrations only.
-- radar_api       the API at runtime: no superuser, no BYPASSRLS, owns nothing.
-- radar_publisher sweeps and marks the outbox across workspaces; nothing else.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'radar_migrator') THEN
        CREATE ROLE radar_migrator LOGIN NOSUPERUSER NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'radar_api') THEN
        CREATE ROLE radar_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'radar_publisher') THEN
        CREATE ROLE radar_publisher LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
END
$$;
