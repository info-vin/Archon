-- Consolidated Migration: 033_seed_nexus_data.sql
-- Covers: 042
-- Purpose: Seed ManagerNexus defaults and AI budget limits.

INSERT INTO public.archon_settings (key, value, category, description, is_system_protected) VALUES 
('marketing_scoring', '{
    "weights": [
        {"key": "VITAL_CONTACT", "label": "Contact Info", "weight": 20},
        {"key": "FUNDING_NEWS", "label": "Funding News", "weight": 30},
        {"key": "JOB_URL", "label": "Hiring Signal", "weight": 15},
        {"key": "TECH_STACK", "label": "Tech Stack Match", "weight": 35}
    ],
    "version": "v1.0.0",
    "updated_by": "System"
}', 'marketing_scoring', 'Marketing Lead Scoring Configuration', false),
('monthly_budget_limit', '100000', 'finance', 'Monthly AI Token Budget (USD)', true)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Register Migration
INSERT INTO schema_migrations (version) VALUES ('033_seed_nexus_data') ON CONFLICT (version) DO NOTHING;
