-- migration/002_create_schema_migrations_table.sql
-- This table tracks which migration scripts have been executed.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    migrated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);
