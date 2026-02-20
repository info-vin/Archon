-- Migration: 024_add_contact_info_to_leads.sql
-- Description: Adds contact info columns to leads table to support Sentinel scoring and Mock Data.
-- Date: 2026-02-06

ALTER TABLE leads
ADD COLUMN IF NOT EXISTS contact_name TEXT,
ADD COLUMN IF NOT EXISTS email TEXT,
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual';

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('024_add_contact_info_to_leads') ON CONFLICT (version) DO NOTHING;
