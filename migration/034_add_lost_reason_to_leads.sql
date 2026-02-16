-- Migration: 034_add_lost_reason_to_leads.sql
-- Description: Adds columns to capture failure reasons for expertise harvesting (EXP-01)
-- Date: 2026-02-16

-- 1. Add columns to leads table
ALTER TABLE public.leads 
ADD COLUMN IF NOT EXISTS lost_reason TEXT,
ADD COLUMN IF NOT EXISTS lost_competitor TEXT;

-- 2. Add comments for clarity
COMMENT ON COLUMN public.leads.lost_reason IS 'Reason why the lead was lost or rejected.';
COMMENT ON COLUMN public.leads.lost_competitor IS 'Competitor the lead chose instead of our solution, if known.';

-- 3. Register Migration
INSERT INTO public.schema_migrations (version) VALUES ('034_add_lost_reason_to_leads') ON CONFLICT (version) DO NOTHING;
