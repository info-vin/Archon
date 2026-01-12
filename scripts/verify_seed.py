import os
import psycopg2
import sys

# This script is designed to run INSIDE the archon-server container
# or locally. It prioritizes DB connection but falls back to API.

def check_db_state():
    db_url = os.environ.get('SUPABASE_DB_URL')
    
    # Try DB connection first, then API
    conn = None
    try:
        if db_url:
            print("Attempting to connect to DB for verification...")
            conn = psycopg2.connect(db_url, connect_timeout=3)
            print("✅ DB connected.")
    except Exception as e:
        print(f"⚠️ DB connection failed: {e}. Falling back to API verification...")

    print("\n🔍 Verifying Database Integrity...")
    
    # 1. Check Profiles Alignment
    print('\n--- 1. Checking Profiles (Should align with Matrix) ---')
    targets = ['Charlie Brown', 'Alice Johnson', 'DevBot']
    rows = []
    
    try:
        from src.server.utils import get_supabase_client
        supabase = get_supabase_client()
        
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT name, role, department FROM profiles WHERE name = ANY(%s)", (targets,))
            rows = cur.fetchall()
            cur.close()
        else:
            # API Fallback
            resp = supabase.table("profiles").select("name, role, department").in_("name", targets).execute()
            rows = [(r['name'], r['role'], r['department']) for r in resp.data] if resp.data else []

        expected = {
            'Charlie Brown': {'role': 'manager', 'dept': 'Marketing'},
            'Alice Johnson': {'role': 'member', 'dept': 'Sales'},
            'DevBot': {'role': 'ai_agent', 'dept': 'AI'}
        }
        
        passed_profiles = True
        found_names = []
        for name, role, dept in rows:
            found_names.append(name)
            exp = expected.get(name)
            if exp:
                if role == exp['role'] and dept == exp['dept']:
                    print(f"✅ {name}: Role={role}, Dept={dept}")
                else:
                    print(f"❌ {name}: Found Role={role}, Dept={dept} | Expected Role={exp['role']}, Dept={exp['dept']}")
                    passed_profiles = False

        if len(found_names) < len(targets):
            print(f"❌ Missing profiles: {set(targets) - set(found_names)}")
            passed_profiles = False

        # 2. Check Auth Users (Requires Admin API)
        print('\n--- 2. Checking Auth Users (Sync Check) ---')
        passed_auth = True
        
        # list_users() returns GoTrueAdminResponse
        auth_resp = supabase.auth.admin.list_users()
        # The list of users is in auth_resp.users (plural) or auth_resp (it's an iterable)
        # Depending on supabase-py version
        users_list = []
        if hasattr(auth_resp, 'users'):
            users_list = auth_resp.users
        elif isinstance(auth_resp, list):
            users_list = auth_resp
        else:
            # Fallback for newer versions
            users_list = getattr(auth_resp, 'users', [])

        found_emails = [u.email for u in users_list]
        
        target_emails = ['admin@archon.com', 'alice@archon.com', 'market.bot@archon.com']
        for email in target_emails:
            if email in found_emails:
                print(f"✅ Auth account found: {email}")
            else:
                print(f"❌ Auth account MISSING: {email}")
                passed_auth = False

    except Exception as e:
        print(f"❌ Verification Error: {e}")
        passed_auth = False
        passed_profiles = False

    if conn: conn.close()
    
    if passed_profiles and passed_auth:
        print("\n🎉 VERIFICATION PASSED: Database state is consistent.")
        sys.exit(0)
    else:
        print("\n⛔ VERIFICATION FAILED: Inconsistencies found.")
        sys.exit(1)

if __name__ == "__main__":
    check_db_state()