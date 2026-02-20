-- migration/014_vector_rls_policy.sql
-- Description: Enable Row-Level Security (RLS) for Vector Store tables to enforce department isolation.
-- Corrected Target Tables: archon_sources, archon_crawled_pages, archon_code_examples.
-- User Table: profiles (not employees).

-- 1. Enable RLS
ALTER TABLE archon_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_crawled_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_code_examples ENABLE ROW LEVEL SECURITY;

-- 2. Policy for archon_sources (Root of Trust)

-- Admin (System Admin & Admin) can see everything
CREATE POLICY admin_all_sources ON archon_sources
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid()::text 
            AND role IN ('system_admin', 'admin')
        )
    );

-- Department Isolation: Users can only see sources from their own department OR 'Public'
CREATE POLICY dept_isolation_read ON archon_sources
    FOR SELECT
    TO authenticated
    USING (
        -- 1. Public content is visible to all
        (metadata->>'department' = 'Public' OR metadata->>'department' IS NULL)
        OR
        -- 2. User's department matches source department
        (metadata->>'department' = (
            SELECT department FROM profiles WHERE id = auth.uid()::text
        ))
        OR
        -- 3. Managers can see everything (Optional, enabling for now for oversight)
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE id = auth.uid()::text 
            AND role IN ('manager', 'project_manager')
        )
    );

-- Write Policy: Users can only insert/update sources for their own department
CREATE POLICY dept_isolation_write ON archon_sources
    FOR INSERT
    TO authenticated
    WITH CHECK (
        metadata->>'department' = (
            SELECT department FROM profiles WHERE id = auth.uid()::text
        )
    );

-- 3. Cascade Policies for Child Tables
-- Inherit visibility from parent source

CREATE POLICY child_pages_isolation ON archon_crawled_pages
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM archon_sources s
            WHERE s.source_id = archon_crawled_pages.source_id
        )
    );

CREATE POLICY child_code_isolation ON archon_code_examples
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM archon_sources s
            WHERE s.source_id = archon_code_examples.source_id
        )
    );