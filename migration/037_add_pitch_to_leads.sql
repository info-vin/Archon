-- Migration: 037_add_pitch_to_leads.sql
-- Description: Adds pitch_content column to leads table to store generated pitches
-- Date: 2026-02-10

ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS pitch_content TEXT;

COMMENT ON COLUMN leads.pitch_content IS 'The AI-generated sales pitch content for this lead';

-- Register migration
INSERT INTO schema_migrations (version) VALUES ('037_add_pitch_to_leads') ON CONFLICT (version) DO NOTHING;
