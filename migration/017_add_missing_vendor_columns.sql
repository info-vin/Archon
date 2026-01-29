-- Migration: 017_add_missing_vendor_columns.sql
-- Description: Adds description, status, and updated_at columns to vendors table.
-- Fixes: Lead Promotion failure due to missing columns.
-- Date: 2026-01-29

ALTER TABLE vendors
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active',
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('017_add_missing_vendor_columns') ON CONFLICT (version) DO NOTHING;
