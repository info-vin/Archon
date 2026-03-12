import glob
import logging
import os
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager

import psycopg2
from psycopg2.extensions import cursor as PGCursor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("init_db")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("src.server.services.auth_service").setLevel(logging.ERROR)

DB_URL = os.getenv("SUPABASE_DB_URL")

try:
    from src.server.services.auth_service import AuthService
    from src.server.utils import get_supabase_client
    HAS_SERVER_DEPS = True
except ImportError:
    HAS_SERVER_DEPS = False

@contextmanager
def db_transaction() -> Generator[PGCursor, None, None]:
    if not DB_URL:
        logger.error("❌ SUPABASE_DB_URL not set.")
        sys.exit(1)

    conn = None
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(DB_URL)
            break
        except psycopg2.OperationalError as e:
            retries -= 1
            if retries == 0:
                logger.error(f"❌ DB Connection failed: {e}")
                sys.exit(1)
            logger.warning(f"Connection failed, retrying... ({retries} left)")
            time.sleep(2)

    if conn is None:
        logger.error("❌ Failed to establish database connection.")
        sys.exit(1)

    try:
        conn.autocommit = False
        with conn.cursor() as cursor:
            yield cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Transaction failed & rolled back: {e}")
        raise e
    finally:
        if conn:
            conn.close()

def is_duplicate_user_error(e: Exception) -> bool:
    err_str = str(e).lower()
    if hasattr(e, 'response') and hasattr(e.response, 'text'):
        err_str += f" {e.response.text.lower()}"
    if hasattr(e, 'message'):
        err_str += f" {str(e.message).lower()}"
    if hasattr(e, 'args') and e.args:
        for arg in e.args:
            err_str += f" {str(arg).lower()}"
    return any(k in err_str for k in ["already registered", "already been registered", "already exists", "422", "unprocessable entity"])

def run_migrations(cursor: PGCursor, migration_dir: str = "migration", exclude: set[str] | None = None) -> None:
    logger.info("Running schema migrations...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY, migrated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)
    cursor.execute("SELECT version FROM schema_migrations")
    applied = {row[0] for row in cursor.fetchall()}
    files = sorted(glob.glob(os.path.join(migration_dir, "0.2.1", "*.sql")))
    exclude = exclude or set()
    skipped_count = 0

    for f_path in files:
        fname = os.path.basename(f_path)
        version_id = os.path.splitext(fname)[0]
        if fname in exclude or version_id in applied:
            skipped_count += 1
            continue
        logger.info(f"Applying: {fname}")
        with open(f_path) as f:
            cursor.execute(f.read())
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT DO NOTHING", (version_id,))
    logger.info(f"✅ Schema migrations checked. ({skipped_count} scripts skipped as already applied)")

def seed_data(cursor: PGCursor) -> None:
    seed_file = "migration/0.2.1/seed_mock_data.sql"
    if os.path.exists(seed_file):
        logger.info(f"🌱 Seeding mock data: {seed_file}")
        with open(seed_file) as f:
            cursor.execute(f.read())

    blog_seed = "migration/0.2.1/seed_blog_posts.sql"
    if os.path.exists(blog_seed):
        logger.info(f"🌱 Seeding blog posts: {blog_seed}")
        with open(blog_seed) as f:
            cursor.execute(f.read())

    logger.info("🔑 Syncing API Keys from Env...")
    api_key_map = [
        ("OPENAI_API_KEY", "OPENAI_API_KEY", "ai", "OpenAI API Key"),
        ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY", "ai", "Anthropic API Key"),
        ("GOOGLE_API_KEY", "GOOGLE_API_KEY", "ai", "Google AI API Key"),
        ("GEMINI_API_KEY", "GEMINI_API_KEY", "ai", "Gemini API Key"),
        ("LOGFIRE_TOKEN", "LOGFIRE_TOKEN", "observability", "Logfire Token"),
    ]
    for env_var, db_key, category, desc in api_key_map:
        val = os.getenv(env_var)
        if val:
            cursor.execute("""
                INSERT INTO archon_settings (key, value, is_encrypted, category, description, updated_at)
                VALUES (%s, %s, false, %s, %s, NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
            """, (db_key, val, category, desc))

    # Bob Workflow Specific Settings
    bob_settings = [
        ("STORY_CANDIDATE_SCORE_THRESHOLD", "80", "marketing", "Minimum score for victory feed"),
        ("NANA_BANANA_MODEL", "gemini-2.0-flash-exp", "marketing", "Image generation model for Nana Banana"),
        ("MARKETING_MODEL", "gemini-2.0-flash", "marketing", "Primary model for marketing content generation"),
        ("SCHEDULER_PROBE_INTERVAL_MINS", "60", "system", "Frequency of system heartbeat probes (minutes)"),
        ("SCHEDULER_PATROL_INTERVAL_MINS", "60", "system", "Frequency of log auto-repair scans (minutes)"),
        ("SCHEDULER_SENTINEL_INTERVAL_HOURS", "12", "business", "Frequency of business risk scans (hours)")
    ]
    for key, val, category, desc in bob_settings:
        cursor.execute("""
            INSERT INTO archon_settings (key, value, is_encrypted, category, description, updated_at)
            VALUES (%s, %s, false, %s, %s, NOW())
            ON CONFLICT (key) DO NOTHING;
        """, (key, val, category, desc))

def sync_auth_users(cursor: PGCursor) -> None:
    if not HAS_SERVER_DEPS:
        logger.warning("⚠️ Skipping Auth Sync (Server dependencies missing)")
        return

    logger.info("🔄 Starting Robust Auth Sync...")
    supabase = get_supabase_client()
    auth_service = AuthService(supabase)
    cursor.execute("SELECT id, email, name, role FROM profiles WHERE status = 'active'")
    profiles = cursor.fetchall()

    DEFAULT_PW = "qwer45tyuiop"
    for p_id, email, name, role in profiles:
        try:
            auth_service.create_user_by_admin(email=email, password=DEFAULT_PW, name=name, role=role)
            logger.info(f"✅ Created Auth User: {email}")
        except Exception as e:
            if not is_duplicate_user_error(e):
                logger.error(f"❌ Failed to create user {email}: {e}")
                continue
            
            # Update password for existing users to match DX-001 requirement
            try:
                auth_uid = _find_auth_id(supabase, email)
                if auth_uid:
                    supabase.auth.admin.update_user_by_id(auth_uid, {"password": DEFAULT_PW})
                    logger.info(f"🔑 Reset password for existing user: {email}")
            except Exception as reset_err:
                logger.warning(f"⚠️ Could not reset password for {email}: {reset_err}")

        auth_uid = _find_auth_id(supabase, email)
        if not auth_uid:
            logger.warning(f"⚠️ Auth ID not found for {email}, skipping fix.")
            continue

        if str(p_id) != str(auth_uid):
            logger.info(f"🛠 Fixing ID mismatch for {email} (DB: {p_id} -> Auth: {auth_uid})")
            _fix_id_mismatch(cursor, str(p_id), str(auth_uid), email, name)

    logger.info("✅ Auth Sync Complete.")

def _find_auth_id(supabase, email: str) -> str | None:
    page = 1
    while True:
        try:
            res = supabase.auth.admin.list_users(page=page, per_page=50)
            users = res if isinstance(res, list) else getattr(res, 'users', [])
            if not users:
                break
            for u in users:
                if u.email == email:
                    return str(u.id)
            if len(users) < 50:
                break
            page += 1
        except Exception:
            return None
    return None

def _fix_id_mismatch(cursor: PGCursor, old_id: str, new_id: str, email: str, name: str) -> None:
    """Safely updates profile ID and re-links tasks without breaking FK constraints."""
    try:
        # Physical Alignment: Standardize ID across Auth and Profiles
        # 1. Update the profile ID itself (the source of truth)
        cursor.execute("UPDATE profiles SET id = %s WHERE email = %s", (new_id, email))
        
        # 2. Update any tasks that were assigned to the OLD (mismatched) ID
        cursor.execute("UPDATE archon_tasks SET assignee_id = %s WHERE assignee_id = %s", (new_id, old_id))
        
        # 3. Fallback: Update by name for legacy task entries
        cursor.execute("UPDATE archon_tasks SET assignee_id = %s WHERE assignee = %s", (new_id, name))
        
        logger.info(f"✅ Successfully aligned physical ID for {email}")
    except Exception as e:
        logger.error(f"❌ Failed to fix physical ID alignment for {email}: {e}")
        # We don't raise here to allow other users to sync, but we log the failure

def print_dev_token() -> None:
    if not HAS_SERVER_DEPS:
        return
    try:
        res = get_supabase_client().auth.sign_in_with_password({"email": "admin@archon.com", "password": "qwer45tyuiop"})
        if res.session:
            print(f"\n🔑 Dev Auto-Login URL: http://localhost:3737/dev-token?token={res.session.access_token}")
    except Exception:
        pass

def main():
    if "--clean" in sys.argv:
        logger.warning("⚠️  CLEAN MODE: Resetting database...")
        with db_transaction() as cursor:
            with open("migration/0.2.1/RESET_DB.sql") as f:
                cursor.execute(f.read())
        logger.info("✅ Database reset.")

    migrate_only = "--migrate-only" in sys.argv

    # 1. Run Migrations & Seeds in one transaction
    with db_transaction() as cursor:
        run_migrations(cursor, exclude={'RESET_DB.sql', 'backup_database.sql', 'complete_setup.sql', 'seed_mock_data.sql'})
        
        if not migrate_only:
            seed_data(cursor)
    
    # 2. Sync Auth Users (External API calls) in a separate step/transaction
    # Note: sync_auth_users manages its own API calls, but we need a cursor for fixing IDs.
    # We start a NEW transaction here to ensure previous locks are released.
    if not migrate_only:
        with db_transaction() as cursor:
            sync_auth_users(cursor)

    print_dev_token()
    logger.info("✅ Database initialized successfully.")

if __name__ == "__main__":
    main()