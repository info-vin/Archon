-- Update Alice and Bob roles to match their personas and enable access to specific features
-- Alice -> sales (access to Sales Intel)
-- Bob -> marketing (access to Brand Hub and Sales Intel)

UPDATE profiles
SET role = 'sales'
WHERE email = 'alice@archon.com';

UPDATE profiles
SET role = 'marketing'
WHERE email = 'bob@archon.com';

-- Register this migration
INSERT INTO schema_migrations (version) VALUES ('011_update_alice_bob_roles') ON CONFLICT (version) DO NOTHING;
