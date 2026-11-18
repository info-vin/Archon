-- 需 Vincent 核准後才可在雲端執行
-- Do not run this file on the cloud database until Vincent approves.
--
-- Why: migration/0.2.3/04_logic_security_rls.sql grants ALL on public.leads,
-- public.archon_tasks, and public.archon_settings to authenticated, which includes
-- TRUNCATE. public.reset_test_database() and public.seed_test_database()
-- (migration/0.2.3/03_logic_functions.sql) have no explicit EXECUTE revoke.
-- PostgreSQL grants EXECUTE to PUBLIC by default, so anon and authenticated can
-- call both functions through the Data API and wipe or reseed those tables.
--
-- PUBLIC is revoked together with anon and authenticated. Revoking only anon and
-- authenticated would leave the default PUBLIC grant in place, and both roles
-- could still execute the functions. That PUBLIC revoke also removes the implicit
-- grant service_role was using. EXECUTE is granted back to service_role so the
-- backend test RPC (service key only) can still call these functions. The
-- function owner keeps EXECUTE. anon and authenticated do not.
--
-- GRANT and REVOKE are no-ops when the privilege is already in the requested
-- state, so this file is safe to re-run.
--
-- Rollback (run only if Vincent decides to restore the previous grants):
-- GRANT TRUNCATE ON TABLE public.leads, public.archon_tasks, public.archon_settings TO authenticated;
-- GRANT EXECUTE ON FUNCTION public.reset_test_database() TO PUBLIC, anon, authenticated;
-- GRANT EXECUTE ON FUNCTION public.seed_test_database() TO PUBLIC, anon, authenticated;
-- REVOKE EXECUTE ON FUNCTION public.reset_test_database() FROM service_role;
-- REVOKE EXECUTE ON FUNCTION public.seed_test_database() FROM service_role;

REVOKE TRUNCATE ON TABLE public.leads, public.archon_tasks, public.archon_settings FROM authenticated;

REVOKE EXECUTE ON FUNCTION public.reset_test_database() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.seed_test_database() FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.reset_test_database() TO service_role;
GRANT EXECUTE ON FUNCTION public.seed_test_database() TO service_role;
