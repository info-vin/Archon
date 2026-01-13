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
    Fallback to Supabase HTTP API if DB connection is unavailable.
    """
    if not HAS_SERVER_DEPS:
        print("Skipping Auth sync (dependencies missing).")
        return

    print("\n🔄 Starting Auth Synchronization...")
    
    try:
        supabase = get_supabase_client()
        auth_service = AuthService(supabase)
        profiles = []
        
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, name, role FROM profiles WHERE status = 'active'")
                profiles = cursor.fetchall()
                cursor.close()
                print(f"Fetched {len(profiles)} profiles via DB.")
            except Exception as e:
                print(f"⚠️ DB fetch failed: {e}. Falling back to API...")
                conn = None
        
        if not conn:
            print("Fetching profiles via Supabase HTTP API...")
            response = supabase.table("profiles").select("id, email, name, role").eq("status", "active").execute()
            if response.data:
                profiles = [(p['id'], p['email'], p['name'], p['role']) for p in response.data]
                print(f"Fetched {len(profiles)} profiles via API.")

        for p_id, email, name, role in profiles:
            try:
                auth_service.create_user_by_admin(email=email, password="password123", name=name, role=role)
                print(f"✅ Synced: {email}")
            except Exception as e:
                # DEBUG: Inspect the exception raw string
                raw_err = str(e)
                # print(f"DEBUG: Error Raw Repr: {repr(raw_err)}")
                
                err_msg_lower = raw_err.lower()
                
                # Robust matching based on Supabase logs and Python exception string
                # 1. Check for explicit "already registered" phrase
                # 2. Check for "422" status code which Supabase uses for duplicates
                # 3. Check for loose words "already" AND ("registered" or "exists")
                
                has_phrase = "already registered" in err_msg_lower or "already exists" in err_msg_lower
                has_422 = "422" in err_msg_lower
                has_loose_words = "already" in err_msg_lower and ("registered" in err_msg_lower or "exists" in err_msg_lower)

                is_duplicate = has_phrase or has_422 or has_loose_words
                
                # print(f"DEBUG: Is Duplicate? {is_duplicate}")

                if is_duplicate:
                    # Strategy A: Resolve ID and Force Update
                    print(f"ℹ️ User {email} exists. Attempting to sync metadata...")
                    auth_uid = find_auth_user_by_email(supabase, email)
                    if auth_uid:
                        try:
                            # print(f"🔍 Resolved Auth ID for {email}: {auth_uid}")
                            update_payload = {
                                "password": "password123",
                                "email_confirm": True,
                                "user_metadata": {"name": name, "role": role}
                            }
                            supabase.auth.admin.update_user_by_id(auth_uid, update_payload)
                            print(f"✅ Updated existing user: {email} (Role: {role})")
                            
                            # Strategy B: Sync Profile ID to match Auth UUID
                            # Verified safe: No tables reference profiles(id) as FK
                            if conn:
                                try:
                                    cursor = conn.cursor()
                                    # Update the ID directly. Since no FKs exist, this is safe.
                                    cursor.execute("UPDATE profiles SET id = %s WHERE email = %s", (auth_uid, email))
                                    conn.commit()
                                    cursor.close()
                                    print(f"✅ Synced Profile ID for {email} to match Auth UUID")
                                except Exception as db_err:
                                    conn.rollback()
                                    print(f"⚠️ Failed to sync Profile ID for {email}: {db_err}")
                            else:
                                # Fallback via API if direct DB conn is not available
                                try:
                                    # Note: Updating ID via API might be restricted by RLS, 
                                    # but we are using service_role key so it should pass.
                                    supabase.table("profiles").update({"id": auth_uid}).eq("email", email).execute()
                                    print(f"✅ Synced Profile ID for {email} to match Auth UUID (via API)")
                                except Exception as api_err:
                                    print(f"⚠️ Failed to sync Profile ID for {email} via API: {api_err}")

                        except Exception as update_err:
                            print(f"❌ Failed to update user {email}: {update_err}")
                    else:
                        print(f"⚠️ Could not find Auth ID for {email} despite 'already registered' error.")
                else:
                    print(f"⚠️ {email} sync failed: {str(e)}")
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
