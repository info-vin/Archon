-- migration/009_fix_rbac_roles_and_permissions.sql

-- 1. Promote Alice and Bob to their specialized roles
-- This aligns the DB data with the roles defined in permissions.py
UPDATE profiles 
SET role = 'sales' 
WHERE email = 'alice@archon.com' AND role = 'member';

UPDATE profiles 
SET role = 'marketing' 
WHERE email = 'bob@archon.com' AND role = 'member';

-- 2. Register Migration
INSERT INTO schema_migrations (version) VALUES ('009_fix_rbac_roles_and_permissions') ON CONFLICT (version) DO NOTHING;
