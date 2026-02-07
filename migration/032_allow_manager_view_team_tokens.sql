-- Migration: 032_allow_manager_view_team_tokens
-- Description: Allow users with MANAGER role to view all token usage for team management.

CREATE POLICY "Managers can view all token usage" ON token_usage
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid()::text AND role = 'manager'
        )
    );

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('032_allow_manager_view_team_tokens') ON CONFLICT (version) DO NOTHING;
