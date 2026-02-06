-- Mock Data for Sentinel Verification
-- Inserts stale leads to trigger alerts

INSERT INTO leads (
    id, 
    company_name, 
    contact_name, 
    email, 
    status, 
    source, 
    enrichment_score, 
    created_at, 
    updated_at
) VALUES 
(
    '00000000-0000-0000-0000-111111111111', 
    'Stale Corp Inc', 
    'Old Contact', 
    'contact@stale.com', 
    'new', 
    'manual', 
    10, 
    NOW() - INTERVAL '30 days', 
    NOW() - INTERVAL '20 days' -- > 14 days old
),
(
    '00000000-0000-0000-0000-222222222222', 
    'Legacy Systems Ltd', 
    'Jane Legacy', 
    'jane@legacy.com', 
    'contacted', 
    'manual', 
    60, -- High score but stale
    NOW() - INTERVAL '60 days', 
    NOW() - INTERVAL '45 days'
)
ON CONFLICT (id) DO UPDATE 
SET updated_at = EXCLUDED.updated_at, status = EXCLUDED.status;
