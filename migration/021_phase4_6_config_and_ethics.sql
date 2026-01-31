-- migration/021_phase4_6_config_and_ethics.sql

-- 1. Create Ethics Events Table for Compliance Logging
CREATE TABLE IF NOT EXISTS archon_ethics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    severity TEXT NOT NULL, -- 'low', 'medium', 'high', 'critical'
    event_type TEXT NOT NULL, -- 'hallucination', 'profanity', 'pii_leak', 'policy_violation'
    description TEXT,
    raw_input TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for Ethics Table
ALTER TABLE archon_ethics_events ENABLE ROW LEVEL SECURITY;

-- Only Managers and Admins can view ethics logs
CREATE POLICY "Allow managers and admins to view ethics logs" ON archon_ethics_events
    FOR SELECT
    USING (auth.role() = 'service_role' OR (SELECT role FROM profiles WHERE id = auth.uid()) IN ('manager', 'system_admin'));

-- Service role can insert logs (backend service)
CREATE POLICY "Allow service role to insert ethics logs" ON archon_ethics_events
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');


-- 2. Insert Model Configurations (Google Defaults)
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('AUDIO_MODEL', 'gemini-1.5-flash', false, 'rag_strategy', 'Model used for voice-to-text transcription'),
('MARKETING_MODEL', 'gemini-1.5-flash', false, 'rag_strategy', 'Model used for generating marketing content (blogs, emails)'),
('NANA_BANANA_MODEL', 'imagen-3', false, 'rag_strategy', 'Model used for image generation services'),
('ENABLE_REAL_ENRICHMENT', 'false', false, 'features', 'Toggle to enable real external API calls for lead enrichment')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

-- Update existing defaults to Google where applicable
UPDATE archon_settings SET value = 'google' WHERE key = 'LLM_PROVIDER';
UPDATE archon_settings SET value = 'gemini-1.5-flash' WHERE key = 'MODEL_CHOICE';

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('021_phase4_6_config_and_ethics') ON CONFLICT (version) DO NOTHING;
