-- migration/027_seed_field_ops_project.sql

-- 1. Ensure 'Field Ops' project exists for Mobile Voice-to-Task
-- We'll create it if it doesn't exist.
-- Assuming 'admin' is the default creator if nobody else is found.

DO $$
DECLARE
    admin_id UUID;
    field_ops_id UUID;
BEGIN
    -- Get an admin ID to be the owner
    SELECT id INTO admin_id FROM auth.users WHERE email = 'admin@example.com' LIMIT 1;
    
    -- Fallback to any user if admin not found (dev env)
    IF admin_id IS NULL THEN
        SELECT id INTO admin_id FROM auth.users LIMIT 1;
    END IF;

    -- Only create if not exists
    IF NOT EXISTS (SELECT 1 FROM archon_projects WHERE title = 'Field Ops') THEN
        INSERT INTO archon_projects (title, description, status, created_by)
        VALUES (
            'Field Ops', 
            '預設專案，用於接收行動端語音日誌自動生成的任務。 (Alice Persona)', 
            'active', 
            admin_id
        ) RETURNING id INTO field_ops_id;
        
        RAISE NOTICE 'Created Field Ops project with ID %', field_ops_id;
    END IF;
END $$;

-- 2. Register migration
INSERT INTO schema_migrations (version) VALUES ('027_seed_field_ops_project') ON CONFLICT (version) DO NOTHING;
