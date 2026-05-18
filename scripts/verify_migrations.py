#!/usr/bin/env python3
"""
verify_migrations.py
Part of Phase 5.2.0 QA Automation (Task 5.2.0.1)

Physically verifies that all SQL migrations and seeds in migration/0.2.2/
can compile and execute from scratch against a local isolated PostgreSQL instance.
Uses the pgvector/pgvector:16 Docker image to support public.vector embeddings.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Try importing psycopg2-binary
try:
    import psycopg2
except ImportError:
    print("❌ Error: 'psycopg2' is not installed. Please run: pip install psycopg2-binary")
    sys.exit(1)

# Configurations
CONTAINER_NAME = "archon-pg-shadow"
PORT = 54321
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "postgres"
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:{PORT}/{DB_NAME}"

# Locate migration folder
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
MIGRATION_DIR = WORKSPACE_DIR / "migration" / "0.2.2"

def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Wrapper around subprocess.run."""
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check)

def cleanup_container():
    """Stops and removes the shadow DB container if it exists."""
    print(f"🧹 Cleaning up existing Docker container '{CONTAINER_NAME}'...")
    try:
        run_cmd(["docker", "rm", "-f", CONTAINER_NAME], check=False)
    except Exception as e:
        print(f"⚠️ Failed to cleanup container: {e}")

def start_shadow_db():
    """Starts the pgvector container and waits for pg_isready."""
    cleanup_container()
    print(f"🚀 Starting shadow database container '{CONTAINER_NAME}' on port {PORT} using pgvector/pgvector:pg16...")
    try:
        run_cmd([
            "docker", "run", "-d",
            "--name", CONTAINER_NAME,
            "-p", f"{PORT}:5432",
            "-e", f"POSTGRES_PASSWORD={DB_PASSWORD}",
            "-e", f"POSTGRES_DB={DB_NAME}",
            "pgvector/pgvector:pg16"
        ])
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Docker container: {e.stderr}")
        sys.exit(1)

    # Wait for PostgreSQL to be ready
    max_retries = 15
    print("⏳ Waiting for shadow database to accept connections...")
    for i in range(max_retries):
        try:
            # First try pg_isready via docker
            res = run_cmd(["docker", "exec", CONTAINER_NAME, "pg_isready"], check=False)
            if res.returncode == 0:
                # Double check with physical psycopg2 connection
                conn = psycopg2.connect(DB_URL)
                conn.close()
                print("🟢 Shadow database is ready!")
                return
        except Exception:
            pass
        time.sleep(1)
        print(f"  [{i+1}/{max_retries}] Retrying connection...")

    print("❌ Error: Timeout waiting for shadow database to start.")
    cleanup_container()
    sys.exit(1)

def get_migration_files() -> list[Path]:
    """Finds and sorts all SQL migration and seed files in migration/0.2.2."""
    if not MIGRATION_DIR.exists():
        print(f"❌ Error: Migration directory does not exist at '{MIGRATION_DIR}'")
        sys.exit(1)

    sql_files = list(MIGRATION_DIR.glob("*.sql"))
    # Exclude reset script as we are running against a clean, new container
    sql_files = [f for f in sql_files if f.name != "RESET_DB.sql"]

    # Sorting logic:
    # 1. Numerically sorted files starting with numbers (e.g. 01_..., 10_...)
    # 2. Other SQL files (e.g. seed_...) sorted alphabetically
    numbered_files = []
    other_files = []

    for f in sql_files:
        basename = f.name
        first_part = basename.split("_")[0]
        if first_part.isdigit():
            numbered_files.append((int(first_part), f))
        else:
            other_files.append(f)

    # Sort numbered files by their integer value
    numbered_files.sort(key=lambda x: x[0])
    sorted_numbered = [f for _, f in numbered_files]

    # Sort other files alphabetically
    other_files.sort(key=lambda x: x.name)

    all_sorted = sorted_numbered + other_files
    print(f"📋 Found {len(all_sorted)} SQL migration and seed files to execute.")
    for idx, f in enumerate(all_sorted, 1):
        print(f"  [{idx:02d}] {f.name}")

    return all_sorted

def execute_migrations(sql_files: list[Path]):
    """Connects to PG and executes all SQL files sequentially."""
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        cur = conn.cursor()

        # Step 1: Pre-install core extensions required by the schema
        print("🔧 Installing required extensions (vector, uuid-ossp, pgcrypto, pg_trgm) matching Supabase schemas...")
        cur.execute("CREATE SCHEMA IF NOT EXISTS extensions;")
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA extensions;')
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto SCHEMA extensions;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA public;")
        
        # Configure search path so that non-prefixed extension functions (e.g. crypt, gen_salt) can be resolved
        print("🔍 Setting search_path to resolve extension functions...")
        cur.execute('ALTER DATABASE postgres SET search_path TO "$user", public, extensions;')
        cur.execute('SET search_path TO "$user", public, extensions;')
        conn.commit()

        # Step 1.5: Create dummy auth schema and users table with all expected columns
        print("👤 Setting up dummy auth schema and users table matching Supabase Auth...")
        cur.execute("CREATE SCHEMA IF NOT EXISTS auth;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auth.users (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                instance_id uuid,
                aud text,
                role text,
                email text,
                encrypted_password text,
                email_confirmed_at timestamp with time zone,
                created_at timestamp with time zone DEFAULT now(),
                updated_at timestamp with time zone DEFAULT now()
            );
        """)
        
        # Step 1.5.5: Create public.schema_migrations table to track migration seeds
        print("📋 Creating public.schema_migrations table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.schema_migrations (
                version varchar(255) PRIMARY KEY,
                inserted_at timestamp with time zone DEFAULT now()
            );
        """)
        
        # Step 1.6: Create dummy auth.uid(), auth.role(), and auth.jwt() functions for Row Level Security policies
        print("🔒 Creating dummy auth.uid(), auth.role(), and auth.jwt() functions for Supabase RLS policies...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION auth.uid()
            RETURNS uuid
            LANGUAGE sql
            STABLE
            AS $$
                SELECT null::uuid;
            $$;
            
            CREATE OR REPLACE FUNCTION auth.role()
            RETURNS text
            LANGUAGE sql
            STABLE
            AS $$
                SELECT 'authenticated'::text;
            $$;
            
            CREATE OR REPLACE FUNCTION auth.jwt()
            RETURNS jsonb
            LANGUAGE sql
            STABLE
            AS $$
                SELECT '{}'::jsonb;
            $$;
        """)
        
        # Step 1.7: Create dummy Supabase system roles for Row Level Security policies
        print("👥 Creating dummy Supabase system roles (anon, authenticated, service_role)...")
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN
                    CREATE ROLE anon;
                END IF;
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN
                    CREATE ROLE authenticated;
                END IF;
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN
                    CREATE ROLE service_role;
                END IF;
            END $$;
        """)
        conn.commit()

        # Step 2: Execute each migration file
        for f in sql_files:
            print(f"⚡ Executing '{f.name}'...")
            with open(f, "r", encoding="utf-8") as file:
                sql_content = file.read()
            
            # Execute entire file inside a single transaction savepoint/try-except
            try:
                cur.execute(sql_content)
                conn.commit()
                print(f"  ✅ '{f.name}' executed successfully.")
            except Exception as e:
                conn.rollback()
                print(f"❌ Error executing migration '{f.name}':\n{e}")
                raise

        print("\n🎉 All migrations and seed files built and seeded successfully!")

        # Step 3: Sanity check key tables exist
        print("🔎 Running schema sanity check...")
        expected_tables = [
            "archon_settings",
            "profiles",
            "archon_sources",
            "archon_crawled_pages",
            "archon_code_examples",
            "archon_projects",
            "archon_tasks",
            "archon_project_sources",
            "archon_document_versions",
            "archon_prompts",
            "archon_crawler_targets"
        ]

        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = {row[0] for row in cur.fetchall()}

        missing_tables = [t for t in expected_tables if t not in existing_tables]
        if missing_tables:
            print(f"❌ Sanity check FAILED. The following expected tables are missing: {missing_tables}")
            raise ValueError(f"Missing core tables: {missing_tables}")

        print("🟢 Schema sanity check PASSED. All core tables exist in 'public' schema.")

    except Exception as e:
        print("\n🚨 Migration verification FAILED!")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def main():
    print("==========================================================")
    print("🔒 Phase 5.2.0: SQL Migrations Verification Pipeline")
    print("==========================================================")
    
    start_shadow_db()
    sql_files = get_migration_files()

    success = False
    try:
        execute_migrations(sql_files)
        success = True
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
    finally:
        cleanup_container()

    if success:
        print("\n🟢 [SUCCESS] Migration validation pipeline completed successfully!")
        sys.exit(0)
    else:
        print("\n🔴 [FAILURE] Migration validation pipeline failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
