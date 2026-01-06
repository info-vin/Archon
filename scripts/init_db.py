import os
import time
import glob
import psycopg2
from urllib.parse import urlparse

# Database connection parameters from environment variables
DB_URL = os.getenv("SUPABASE_DB_URL", "postgresql://postgres:postgres@localhost:54322/postgres")

def get_db_connection():
    """Establishes a connection to the database with retry logic."""
    retries = 30
    while retries > 0:
        try:
            print(f"Attempting to connect to database... ({retries} retries left)")
            conn = psycopg2.connect(DB_URL)
            return conn
        except psycopg2.OperationalError as e:
            print(f"Connection failed: {e}")
            retries -= 1
            time.sleep(2)
    raise Exception("Could not connect to the database after multiple attempts.")

def ensure_schema_migrations_table(cursor):
    """Ensures the schema_migrations table exists."""
    print("Ensuring schema_migrations table exists...")
    # We check manually or run 002 script, but to be safe and strictly follow logic,
    # we'll just execute a safe CREATE TABLE IF NOT EXISTS here as a bootstrap.
    # The 002 script will still run idempotently later.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            migrated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)

def get_applied_migrations(cursor):
    """Retrieves a set of already applied migration versions."""
    cursor.execute("SELECT version FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}

def run_migration_file(conn, cursor, file_path):
    """Reads and executes a single SQL migration file."""
    filename = os.path.basename(file_path)
    version_id = os.path.splitext(filename)[0] # e.g., "000_unified_schema"

    print(f"Running migration: {filename} ...")
    
    with open(file_path, 'r') as f:
        sql = f.read()

    try:
        # Execute the SQL content
        cursor.execute(sql)
        
        # Explicitly register the version if the SQL script didn't do it
        # (Although our SOP says SQL files should do it, we double-bag it here for safety, 
        # using ON CONFLICT to avoid errors if the script DID do it)
        cursor.execute("""
            INSERT INTO schema_migrations (version) 
            VALUES (%s) 
            ON CONFLICT (version) DO NOTHING
        """, (version_id,))
        
        conn.commit()
        print(f"✅ Successfully applied: {filename}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to apply {filename}: {e}")
        raise e

def main():
    conn = get_db_connection()
    conn.autocommit = False # We manage transactions manually
    cursor = conn.cursor()

    try:
        # 1. Bootstrap migration tracking
        ensure_schema_migrations_table(cursor)
        conn.commit()

        # 2. Get current state
        applied_versions = get_applied_migrations(cursor)
        print(f"Found {len(applied_versions)} applied migrations.")

        # 3. Scan for SQL files
        # We sort alphabetically to ensure 000 runs before 001, etc.
        migration_files = sorted(glob.glob("migration/*.sql"))
        
        # Filter out utility scripts that shouldn't be run automatically if any
        # For now, we assume all .sql in migration/ are valid migrations or seeds
        # Except maybe backup/reset scripts if they exist and match *.sql
        # Let's filter out specific ones if needed.
        # Based on file list: RESET_DB.sql, backup_database.sql, complete_setup.sql might be dangerous.
        
        EXCLUDED_FILES = [
            'RESET_DB.sql', 
            'backup_database.sql', 
            'complete_setup.sql' # This seems to be a legacy mega-script
        ]

        for file_path in migration_files:
            filename = os.path.basename(file_path)
            
            if filename in EXCLUDED_FILES:
                print(f"Skipping excluded file: {filename}")
                continue

            version_id = os.path.splitext(filename)[0]

            if version_id in applied_versions:
                print(f"Skipping already applied: {filename}")
                continue
            
            # Special handling for seed files: 
            # If we want seeds to run ALWAYS (to update data), we might check logic here.
            # But per our SOP, seeds should be idempotent and tracked by version.
            # If seed_mock_data.sql changes, we usually rename it or assume it's a one-time thing.
            # However, if user wants to re-run seeds, they should probably clear the migration entry manually?
            # For now, we treat seeds like normal migrations: run once.
            
            run_migration_file(conn, cursor, file_path)

        print("\n🎉 All migrations applied successfully!")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
