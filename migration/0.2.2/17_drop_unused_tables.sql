-- Migration 17: Clean up orphaned tables
-- These tables were planned in earlier phases but their functionality 
-- was either merged into other tables (e.g., market_insights into leads) 
-- or deprecated to keep the system lean.

DROP TABLE IF EXISTS public.subscriptions CASCADE;
DROP TABLE IF EXISTS public.market_insights CASCADE;
DROP TABLE IF EXISTS public.customers CASCADE;
