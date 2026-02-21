---
description: How to perform a Semantic True Consolidation for Database Migrations using pg_dump
---
# Database Semantic Consolidation Workflow

When the database migration folder (`migration/`) becomes too cluttered with linear `000_...`, `001_...` scripts that create and later alter the same tables, you should perform a "Semantic True Consolidation". This collapses all scripts into a few clean, modular files representing the final state of the database.

## Prerequisites
- Docker backend must be running.
- You should have already verified that the current database schema state is complete and correct.

## Step 1: Extract the Current Database Schema
Use `pg_dump` to extract the full structural definition of the database currently running in Docker, inside the `archon-db` container.

```bash
docker exec archon-db pg_dump -U postgres -d postgres --schema-only -n public > temp_schema.sql
```

## Step 2: Slice the Dump into Domains
Create a `split_dump.py` script that parses the `temp_schema.sql` and intelligently strips out redundant or harmful `psql` meta-commands (e.g. `\restrict`, `SET search_path`), and replaces `CREATE FUNCTION` with `CREATE OR REPLACE FUNCTION` to ensure idempotency. Then assign the parsed commands into target files based on standard architectural domains:

1. `01_core_auth_users.sql` (Settings, Extensions, and Core User Profiles)
2. `02_crm_and_knowledge.sql` (Leads, Vendors, Crawled Docs, Articles)
3. `03_projects_and_tasks.sql` (Projects, Tasks, Document Versions)
4. `04_system_and_logs.sql` (System Audits, Token Usage, Ethics Events)
5. `05_policies_and_functions.sql` (All foreign key Constraints, RLS Policies, Functions, and Triggers)

*Important Code Adjustments for the Python Splitter*:
- Discard the `schema_migrations` table logic since this is usually handled by the init tracker.
- Filter out `SCHEMA public` commands to prevent `DuplicateSchema` errors on reset.

## Step 3: Run the Python Slicer
Execute the script to generate the 5 SQL files directly inside the new version folder:
```bash
python split_dump.py
```

## Step 4: Ensure the Old Data and Custom Types are Deleted in `RESET_DB.sql`
A critical failure point of migrations is forgetting to drop newly created custom ENUMs or tables in `RESET_DB.sql`. Before running the initialization:
1. Verify that all custom types (e.g. `change_status`, `task_status`) are explicitly dropped via `DROP TYPE IF EXISTS ... CASCADE;`.
2. Ensure every single custom table in the 5 domains is listed in the `DROP TABLE IF EXISTS ... CASCADE;` statement.
3. Remove functions that were changed to `CREATE OR REPLACE FUNCTION` from the drop list since they will safely overwrite themselves.

## Step 5: Test the Consolidation
Run the init script with the `--clean` flag to start from a blank slate.
```bash
docker exec archon-server python /app/scripts/init_db.py --clean
```

## Step 6: Verify Backend Tests
Never assume the schema is semantically sound just because it loaded. Run the full backend test suite to verify types and relationships:
```bash
make test-be
```

## Step 7: Delete Obsolete Files 
Once tests pass, permanently delete the old migration folder (e.g., `0.2.0/`), update your `CONTRIBUTING` documentation, and commit the new branch cleanly.
```bash
rm temp_schema.sql split_dump.py
```
