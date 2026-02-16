-- Migration: 040_modernize_document_versions_constraint.sql
-- Description: Modernize the version control constraint to support system-wide auditing (Librarian, Prompts, Settings) (GAP-022 Follow-up)
-- Date: 2026-02-11

-- 1. Drop the outdated constraint that forces project or task link
ALTER TABLE public.archon_document_versions 
DROP CONSTRAINT IF EXISTS chk_project_or_task;

-- 2. Add a more flexible constraint that allows:
--    a) Traditional Project/Task versioning (Standard)
--    b) System-level auditing via field_name or document_id (Librarian/Admin)
ALTER TABLE public.archon_document_versions
ADD CONSTRAINT chk_version_identity 
CHECK (
    (project_id IS NOT NULL) OR 
    (task_id IS NOT NULL) OR 
    (document_id IS NOT NULL) OR
    (field_name IN ('sales_pitch', 'web_research', 'knowledge_file', 'system_prompt', 'system_setting'))
);

-- Comment for documentation
COMMENT ON CONSTRAINT chk_version_identity ON public.archon_document_versions 
IS 'Ensures every audit entry is traceable to either a Project, Task, Document, or a recognized System Category.';

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('040_modernize_document_versions_constraint') ON CONFLICT (version) DO NOTHING;
