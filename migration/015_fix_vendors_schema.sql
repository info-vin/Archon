-- Migration: 015_fix_vendors_schema.sql
-- Description: Adds missing contact_email column to vendors table to support Lead Promotion.
-- Fixes: FB-01 (Promote Lead Failure)
-- Date: 2026-01-29

-- 1. Add contact_email to vendors if it doesn't exist
ALTER TABLE vendors
ADD COLUMN IF NOT EXISTS contact_email TEXT;

-- 2. Add owner_id if it doesn't exist (Safety check, should be in 008)
ALTER TABLE vendors
ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES auth.users(id);

-- 3. Register Migration
INSERT INTO schema_migrations (version) VALUES ('015_fix_vendors_schema') ON CONFLICT (version) DO NOTHING;
