-- migration/temp_fix_seq.sql
-- 物理修復：授權所有核心序列權限給 API 與 服務角色
-- 確保 LibrarianService (service_role) 具備物理寫入能力

-- 1. 授權基礎 USAGE 與 SELECT 權限
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role, postgres;

-- 2. 針對報錯的特定序列進行全權限加固 (Physical Hardening)
GRANT ALL PRIVILEGES ON SEQUENCE public.archon_crawled_pages_id_seq TO service_role, postgres;
GRANT ALL PRIVILEGES ON SEQUENCE public.archon_code_examples_id_seq TO service_role, postgres;

-- 3. 確保未來新增的序列也能自動獲得授權
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO service_role, postgres;
