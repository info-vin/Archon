-- Seed default marketing scoring settings for ManagerNexus
-- Idempotent: uses ON CONFLICT DO NOTHING

INSERT INTO archon_settings (key, value, category, description, is_system_protected)
VALUES 
('marketing_scoring', '{
    "weights": [
        {"key": "VITAL_CONTACT", "label": "Contact Info", "weight": 20},
        {"key": "FUNDING_NEWS", "label": "Funding News", "weight": 30},
        {"key": "JOB_URL", "label": "Hiring Signal", "weight": 15},
        {"key": "TECH_STACK", "label": "Tech Stack Match", "weight": 35}
    ],
    "version": "v1.0.0",
    "updated_by": "System"
}', 'marketing_scoring', 'Marketing Lead Scoring Configuration', false)
ON CONFLICT (key) DO NOTHING;

-- Seed default monthly budget for AI usage
INSERT INTO archon_settings (key, value, category, description, is_system_protected)
VALUES 
('monthly_budget_limit', '100000', 'finance', 'Monthly AI Token Budget (USD)', true)
ON CONFLICT (key) DO NOTHING;

-- Register migration version
INSERT INTO schema_migrations (version) VALUES ('042_seed_manager_nexus_settings') ON CONFLICT (version) DO NOTHING;
