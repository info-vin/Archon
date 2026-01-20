-- migration/008_system_correction_phase44.sql

-- 1. Enhance Vendors Table (Sales Nexus)
-- Adding fields to support the sales workflow
ALTER TABLE vendors
ADD COLUMN IF NOT EXISTS pain_points TEXT,
ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'qualified',
ADD COLUMN IF NOT EXISTS contact_info JSONB DEFAULT '{}'::jsonb;

-- 2. Enhance Tasks Table (Management)
-- Adding time tracking fields
ALTER TABLE archon_tasks
ADD COLUMN IF NOT EXISTS estimated_hours FLOAT DEFAULT 0,
ADD COLUMN IF NOT EXISTS actual_hours FLOAT DEFAULT 0;

-- 3. Enhance Leads Table (Sales Nexus)
-- Adding link to projects and contact details
ALTER TABLE leads
ADD COLUMN IF NOT EXISTS contact_name TEXT,
ADD COLUMN IF NOT EXISTS contact_email TEXT,
ADD COLUMN IF NOT EXISTS contact_phone TEXT,
ADD COLUMN IF NOT EXISTS linked_project_id UUID REFERENCES archon_projects(id),
ADD COLUMN IF NOT EXISTS last_contacted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS next_followup_date TIMESTAMPTZ;

-- Ensure no duplicate leads from same URL
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_source_url ON leads(source_job_url);

-- 4. Inject "Rebrand" Task for Charlie (Project ECITON)
-- This puts the task on the board for the Manager to see
INSERT INTO archon_tasks (title, description, assignee, status, priority, due_date)
VALUES (
    '[REBRAND] Implement Project Eciton Identity',
    '**Visual Specs**:
* **Style**: Geometric Node-Link Diagram.
* **Palette**: Cyan (#00f2ff) to Purple (#a855f7).
* **Animation**: Pulse effect.

**Action**:
* Assign to **DevBot** to generate `logo-eciton.svg`.',
    'DevBot',
    'todo',
    'high',
    NOW() + INTERVAL '3 days'
);

-- 5. Register Migration Version
INSERT INTO schema_migrations (version) VALUES ('008_system_correction_phase44') ON CONFLICT (version) DO NOTHING;
