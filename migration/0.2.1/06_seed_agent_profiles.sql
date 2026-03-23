-- Migration: 06_seed_agent_profiles.sql
-- Description: Physically grounding AI Agent identities in the profiles table for Phase 4.6.15.
-- Date: 2026-03-23

-- 1. Insert/Sync Archon AI Agents into public.profiles
-- We use fixed UUIDs to ensure traceability across restarts and service syncs.
-- These UUIDs match the name_map in token_usage_service.py (Phase 4.6.15).

INSERT INTO public.profiles (id, name, email, role, status, created_at)
VALUES 
(
    'e1682371-0000-0000-0000-000000000000', 
    'Archon DevBot', 
    'devbot@archon.ai', 
    'agent', 
    'active', 
    NOW()
),
(
    'a11ce000-0000-0000-0000-000000000000', 
    'Archon MarketBot', 
    'marketbot@archon.ai', 
    'marketing', 
    'active', 
    NOW()
),
(
    'b0b00000-0000-0000-0000-000000000000', 
    'Archon Librarian', 
    'librarian@archon.ai', 
    'agent', 
    'active', 
    NOW()
),
(
    'p0b00000-0000-0000-0000-000000000000', 
    'Archon POBot', 
    'pobot@archon.ai', 
    'agent', 
    'active', 
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    role = EXCLUDED.role,
    status = EXCLUDED.status;

-- 2. Audit Log (Grounded verification)
-- Records the physical activation of Phase 4.6.15 Agent Governance.
INSERT INTO public.archon_logs (level, message, source, details)
VALUES (
    'INFO', 
    'Physical Identity Sync: Phase 4.6.15 Agent profiles established.', 
    'system', 
    '{"agents": ["DevBot", "MarketBot", "Librarian", "POBot"], "governance": "Poisson Gate Ready"}'
);
