CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create specific role for backend service
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'fitmate_user') THEN
      CREATE ROLE fitmate_user WITH LOGIN PASSWORD 'fitmate_secure_pass';
   END IF;
END
$do$;


-- Create a schema for our app data to separate it from default public schema
CREATE SCHEMA IF NOT EXISTS fitmate;

-- We assume PostgreSQL is used for admin tracking/logs in dual-DB setup
CREATE TABLE IF NOT EXISTS fitmate.admin_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_username VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    target_collection VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Security Hardening: Enable Row Level Security (RLS)
ALTER TABLE fitmate.admin_logs ENABLE ROW LEVEL SECURITY;

-- Creating a policy:
-- Only the "fitmate_user" role (which FastAPI uses) can select and insert logs.
-- This ensures that even if another user gets DB access, they cannot tamper with logs unless they assume the correct role.
CREATE POLICY admin_logs_policy ON fitmate.admin_logs
    FOR ALL
    TO fitmate_user
    USING (true)
    WITH CHECK (true);

-- Revoke default public access just in case
REVOKE ALL ON fitmate.admin_logs FROM PUBLIC;
GRANT ALL ON SCHEMA fitmate TO fitmate_user;
GRANT ALL ON fitmate.admin_logs TO fitmate_user;
