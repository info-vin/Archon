import os
import time
import glob
import psycopg2
from urllib.parse import urlparse

# Import AuthService for account synchronization
# Note: PYTHONPATH must be set to '.' when running this script
try:
    from src.server.services.auth_service import AuthService
    from src.server.utils import get_supabase_client
    HAS_SERVER_DEPS = True
except ImportError:
    print("Warning: Could not import server dependencies. Auth sync will be skipped.")
    HAS_SERVER_DEPS = False

# Database connection parameters from environment variables
DB_URL = os.getenv("SUPABASE_DB_URL")

if not DB_URL:
    print("❌ Error: SUPABASE_DB_URL environment variable is not set.")
    print("Please add it to your .env file. Example:")
    print("SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres")
    exit(1)

def get_db_connection():
    """Establishes a connection to the database with retry logic."""
    retries = 5
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

def find_auth_user_by_email(supabase, email):
    """
    Finds a user's UUID in the Auth system by email.
    Note: 'list_users' might return pagination objects depending on client version.
    """
    try:
        page = 1
        per_page = 50
        while True:
            # Depending on the supabase-py/gotrue-py version, this might return a list or an object
            response = supabase.auth.admin.list_users(page=page, per_page=per_page)

            # Handle different response structures gracefully
            users = response if isinstance(response, list) else getattr(response, 'users', [])

            if not users:
                break

            for user in users:
                if user.email == email:
                    return user.id

            if len(users) < per_page:
                break
            page += 1
    except Exception as e:
        print(f"⚠️ Error listing users to find {email}: {e}")
    return None

def sync_profiles_to_auth(conn):
    """
    Reads profiles and ensures they exist in auth.users.
    Handles FK constraints by temporarily unlinking tasks if IDs need to be updated.
    """
    if not HAS_SERVER_DEPS:
        print("Skipping Auth sync (dependencies missing).")
        return

    print("\n🔄 Starting Robust Auth Sync...")
    
    try:
        supabase = get_supabase_client()
        auth_service = AuthService(supabase)
        
        # We need a fresh connection if the passed one is None or closed
        # But to be safe, we use the passed conn if valid
        cursor = conn.cursor() if conn else None
        
        # Fetch profiles from DB directly to be sure about IDs
        profiles = []
        if cursor:
            try:
                cursor.execute("SELECT id, email, name, role FROM profiles WHERE status = 'active'")
                profiles = cursor.fetchall() # List of tuples
                print(f"Fetched {len(profiles)} profiles via DB.")
            except Exception as e:
                print(f"⚠️ DB fetch failed: {e}")
        
        # Iterate and Sync
        for p_id, email, name, role in profiles:
            try:
                # 1. Create User in Auth if not exists (Idempotent call via Service)
                try:
                    auth_service.create_user_by_admin(email=email, password="password123", name=name, role=role)
                    print(f"✅ Created Auth User: {email}")
                except Exception as e:
                    # Ignore "already registered" errors, we will sync IDs next
                    if "already registered" not in str(e) and "already exists" not in str(e):
                        print(f"⚠️ Creation error for {email}: {e}")

                # 2. Resolve Auth UUID
                auth_uid = find_auth_user_by_email(supabase, email)
                if not auth_uid:
                    print(f"⚠️ Could not find Auth UUID for {email}. Skipping ID sync.")
                    continue

                # 3. Check for ID Mismatch
                # p_id from DB is the current primary key
                if str(p_id) != str(auth_uid):
                    print(f"   🛠 ID Mismatch for {email} (DB: {p_id} vs Auth: {auth_uid}). Fixing...")
                    
                    if cursor:
                        try:
                            # A. Unlink Tasks (set assignee_id to NULL)
                            cursor.execute("UPDATE archon_tasks SET assignee_id = NULL WHERE assignee_id = %s", (str(p_id),))
                            
                            # B. Update Profile ID
                            cursor.execute("UPDATE profiles SET id = %s WHERE email = %s", (auth_uid, email))
                            
                            # C. Relink Tasks (by Name)
                            # We assume the profile name matches the task assignee name
                            cursor.execute("UPDATE archon_tasks SET assignee_id = %s WHERE assignee = %s", (auth_uid, name))
                            
                            conn.commit()
                            print(f"   ✅ Successfully synced ID for {email}")
                        except Exception as db_err:
                            conn.rollback()
                            print(f"   ❌ Failed to sync ID for {email}: {db_err}")
                else:
                    print(f"   ✅ IDs match for {email}")

            except Exception as e:
                print(f"❌ Error processing {email}: {e}")
                
        print("✅ Auth Sync Complete.")
        
    except Exception as e:
        print(f"❌ Auth Sync Fatal Error: {e}")

def main():
    conn = None
    try:
        print("Attempting DB connection for migrations...")
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        ensure_schema_migrations_table(cursor)
        conn.commit()
        
        applied = get_applied_migrations(cursor)
        migration_files = sorted(glob.glob("migration/*.sql"))
        EXCLUDED = ['RESET_DB.sql', 'backup_database.sql', 'complete_setup.sql']

        for f in migration_files:
            fname = os.path.basename(f)
            if fname in EXCLUDED: continue
            vid = os.path.splitext(fname)[0]
            if vid in applied: continue
            run_migration_file(conn, cursor, f)
        
        conn.commit()
        print("\n🎉 SQL migrations applied!")
    except Exception as e:
        print(f"\n⚠️ SQL Migrations SKIPPED: {e}")
        print("Please run migrations manually in Supabase SQL Editor.")

    sync_profiles_to_auth(conn)
    if conn: conn.close()

if __name__ == "__main__":
    main()
