-- Seed Google Gemini API Crawler Targets for Automated Monitoring
-- Targets: Deprecations and Troubleshooting documentation
-- Frequency: bi-weekly
-- Department: Engineering
-- Date: 2026-05-14

INSERT INTO public.archon_crawler_targets (
    target_url, 
    description, 
    whitelist, 
    update_frequency, 
    department, 
    is_active
) VALUES (
    'https://ai.google.dev/gemini-api/docs/deprecations?hl=zh-tw',
    'Gemini API Deprecations Documentation',
    ARRAY['ai.google.dev/gemini-api/docs/deprecations'],
    'bi-weekly',
    'Engineering',
    true
), (
    'https://ai.google.dev/gemini-api/docs/troubleshooting?hl=zh-tw',
    'Gemini API Troubleshooting & Rate Limits Documentation',
    ARRAY['ai.google.dev/gemini-api/docs/troubleshooting'],
    'bi-weekly',
    'Engineering',
    true
)
ON CONFLICT (target_url) DO UPDATE SET
    whitelist = EXCLUDED.whitelist,
    update_frequency = EXCLUDED.update_frequency,
    department = EXCLUDED.department,
    is_active = EXCLUDED.is_active;

-- Register migration version
INSERT INTO public.schema_migrations (version) 
VALUES ('18_seed_crawler_targets') 
ON CONFLICT (version) DO NOTHING;
