-- 20260920_add_telegram_proxy_setting.sql
-- Description: Add TELEGRAM_PROXY_URL to archon_settings to bypass HF Egress Firewall (Phase 5.11.20)

INSERT INTO public.archon_settings (key, value, is_encrypted, category, description, is_system_protected, updated_at)
VALUES 
    ('TELEGRAM_PROXY_URL', 'https://archon-enduser.vercel.app/api/telegram', false, 'system', 'Vercel Proxy URL for Telegram Egress Firewall bypass', false, NOW())
ON CONFLICT (key) DO UPDATE 
SET 
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at = NOW();
