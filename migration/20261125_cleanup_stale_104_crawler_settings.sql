-- Migration: 20261125_cleanup_stale_104_crawler_settings.sql
-- Purpose: Remove unused legacy 104 URL keys from archon_settings to keep crawler config SSOT-clean.
-- Idempotent: DELETE WHERE key IN (...) + schema_migrations ON CONFLICT DO NOTHING.

BEGIN;

DELETE FROM public.archon_settings
WHERE key IN ('CRAWLER_104_SEARCH_API', 'CRAWLER_104_DETAIL_API');

INSERT INTO public.schema_migrations (version)
VALUES ('20261125_cleanup_stale_104_crawler_settings')
ON CONFLICT (version) DO NOTHING;

COMMIT;
