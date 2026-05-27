#!/usr/bin/env python3
import os
import sys
import time
import json
import asyncio
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

# Try importing psycopg2-binary
try:
    import psycopg2
except ImportError:
    psycopg2 = None

# ANSI color codes for premium output
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR / "python"))
sys.path.insert(0, str(WORKSPACE_DIR))

# --- Verification Logic for Migrations ---
def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check)

def cleanup_container(container_name):
    print(f"🧹 Cleaning up existing Docker container '{container_name}'...")
    try:
        run_cmd(["docker", "rm", "-f", container_name], check=False)
    except Exception as e:
        print(f"⚠️ Failed to cleanup container: {e}")

def run_migrations_verification():
    print(f"\n{CYAN}=========================================================={NC}")
    print(f"{CYAN}🔒 SQL Migrations Verification Pipeline{NC}")
    print(f"{CYAN}=========================================================={NC}")
    
    if psycopg2 is None:
        print("❌ Error: 'psycopg2' is not installed. Please run: pip install psycopg2-binary")
        return False

    container_name = "archon-pg-shadow"
    port = 54321
    db_user = "postgres"
    db_password = "postgres"
    db_name = "postgres"
    db_url = f"postgresql://{db_user}:{db_password}@localhost:{port}/{db_name}"
    migration_dir = WORKSPACE_DIR / "migration" / "0.2.2"

    cleanup_container(container_name)
    print(f"🚀 Starting shadow database container '{container_name}' on port {port}...")
    try:
        run_cmd([
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{port}:5432",
            "-e", f"POSTGRES_PASSWORD={db_password}",
            "-e", f"POSTGRES_DB={db_name}",
            "pgvector/pgvector:pg16"
        ])
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Docker container: {e.stderr}")
        return False

    max_retries = 15
    print("⏳ Waiting for shadow database to accept connections...")
    ready = False
    for i in range(max_retries):
        try:
            res = run_cmd(["docker", "exec", container_name, "pg_isready"], check=False)
            if res.returncode == 0:
                conn = psycopg2.connect(db_url)
                conn.close()
                print("🟢 Shadow database is ready!")
                ready = True
                break
        except Exception:
            pass
        time.sleep(1)
        print(f"  [{i+1}/{max_retries}] Retrying connection...")

    if not ready:
        print("❌ Error: Timeout waiting for shadow database to start.")
        cleanup_container(container_name)
        return False

    if not migration_dir.exists():
        print(f"❌ Error: Migration directory does not exist at '{migration_dir}'")
        cleanup_container(container_name)
        return False

    sql_files = list(migration_dir.glob("*.sql"))
    sql_files = [f for f in sql_files if f.name != "RESET_DB.sql"]

    numbered_files = []
    other_files = []
    for f in sql_files:
        basename = f.name
        first_part = basename.split("_")[0]
        if first_part.isdigit():
            numbered_files.append((int(first_part), f))
        else:
            other_files.append(f)

    numbered_files.sort(key=lambda x: x[0])
    sorted_numbered = [f for _, f in numbered_files]
    other_files.sort(key=lambda x: x.name)
    all_sorted = sorted_numbered + other_files

    print(f"📋 Found {len(all_sorted)} SQL migration and seed files to execute.")

    conn = None
    success = False
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor()

        print("🔧 Installing required extensions...")
        cur.execute("CREATE SCHEMA IF NOT EXISTS extensions;")
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA extensions;')
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto SCHEMA extensions;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA public;")
        
        cur.execute('ALTER DATABASE postgres SET search_path TO "$user", public, extensions;')
        cur.execute('SET search_path TO "$user", public, extensions;')
        conn.commit()

        print("👤 Setting up dummy auth schema and users table...")
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
        
        print("📋 Creating public.schema_migrations table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.schema_migrations (
                version varchar(255) PRIMARY KEY,
                inserted_at timestamp with time zone DEFAULT now()
            );
        """)
        
        print("🔒 Creating dummy auth functions for RLS...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$ SELECT null::uuid; $$;
            CREATE OR REPLACE FUNCTION auth.role() RETURNS text LANGUAGE sql STABLE AS $$ SELECT 'authenticated'::text; $$;
            CREATE OR REPLACE FUNCTION auth.jwt() RETURNS jsonb LANGUAGE sql STABLE AS $$ SELECT '{}'::jsonb; $$;
        """)
        
        print("👥 Creating dummy Supabase system roles...")
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon; END IF;
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticated') THEN CREATE ROLE authenticated; END IF;
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'service_role') THEN CREATE ROLE service_role; END IF;
            END $$;
        """)
        conn.commit()

        for f in all_sorted:
            print(f"⚡ Executing '{f.name}'...")
            with open(f, "r", encoding="utf-8") as file:
                sql_content = file.read()
            try:
                cur.execute(sql_content)
                conn.commit()
                print(f"  ✅ '{f.name}' executed successfully.")
            except Exception as e:
                conn.rollback()
                print(f"❌ Error executing migration '{f.name}':\n{e}")
                raise

        print("\n🔎 Running schema sanity check...")
        expected_tables = [
            "archon_settings", "profiles", "archon_sources", "archon_crawled_pages",
            "archon_code_examples", "archon_projects", "archon_tasks", "archon_project_sources",
            "archon_document_versions", "archon_prompts", "archon_crawler_targets"
        ]
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        existing_tables = {row[0] for row in cur.fetchall()}
        missing_tables = [t for t in expected_tables if t not in existing_tables]
        if missing_tables:
            print(f"❌ Sanity check FAILED. Expected tables missing: {missing_tables}")
            raise ValueError(f"Missing core tables: {missing_tables}")

        print("🟢 Schema sanity check PASSED.")
        success = True
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
    finally:
        if conn:
            conn.close()
        cleanup_container(container_name)

    return success


# --- Verification Logic for MCP ---
def run_mcp_verification():
    print(f"\n{CYAN}=========================================================={NC}")
    print(f"{CYAN}🔍 MCP Health & Tool Schema Audit{NC}")
    print(f"{CYAN}=========================================================={NC}")

    mcp_port = os.getenv("ARCHON_MCP_PORT", "8051")
    mcp_url = f"http://localhost:{mcp_port}"
    health_url = f"{mcp_url}/health"
    rpc_url = f"{mcp_url}/rpc"

    server_process = None
    already_running = False

    try:
        req = urllib.request.Request(health_url, method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("status") == "healthy":
                    print(f"{GREEN}🟢 Connected to already running MCP Server!{NC}")
                    already_running = True
    except Exception:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        try:
            s.connect(("127.0.0.1", int(mcp_port)))
            s.close()
            print(f"{GREEN}🟢 Connected to already running MCP Server (Port {mcp_port} occupied)!{NC}")
            already_running = True
        except Exception:
            print("MCP Server is not running. Launching...")

    if not already_running:
        python_dir = WORKSPACE_DIR / "python"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(python_dir) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
        env["ARCHON_MCP_PORT"] = mcp_port
        
        server_process = subprocess.Popen(
            [sys.executable, "-m", "src.mcp_server.mcp_server"],
            cwd=str(python_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        startup_timeout = 15.0
        start_time = time.time()
        connected = False
        while time.time() - start_time < startup_timeout:
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                print(f"{RED}🔴 MCP Server crashed on startup!{NC}")
                return False
            try:
                req = urllib.request.Request(health_url, method="GET")
                with urllib.request.urlopen(req, timeout=1.0) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        if data.get("status") == "healthy":
                            connected = True
                            break
            except Exception:
                pass
            time.sleep(0.5)
            
        if not connected:
            print(f"{RED}🔴 Timeout waiting for MCP Server to start!{NC}")
            server_process.terminate()
            return False
        print(f"{GREEN}🟢 MCP Server started successfully!{NC}")

    audit_failed = False
    try:
        rpc_payload = {"jsonrpc": "2.0", "method": "list_tools", "params": {}, "id": 1}
        headers = {"Content-Type": "application/json", "X-Agent-Type": "admin"}
        req = urllib.request.Request(rpc_url, data=json.dumps(rpc_payload).encode("utf-8"), headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
        if "error" in res_data:
            print(f"{RED}🔴 RPC list_tools call failed: {res_data['error']}{NC}")
            audit_failed = True
        else:
            tools = res_data.get("result", [])
            print(f"Found {len(tools)} registered tools in MCP Registry.")
            if not tools:
                audit_failed = True
            for idx, t in enumerate(tools, 1):
                func = t.get("function", {})
                name = func.get("name")
                desc = func.get("description")
                params = func.get("parameters", {})
                print(f"[{idx}/{len(tools)}] Auditing Tool: {CYAN}{name}{NC}")
                if not name or not isinstance(params, dict) or params.get("type") != "object":
                    audit_failed = True
                    continue
                print(f"  {GREEN}✓ Tool '{name}' schema syntactically valid!{NC}")
    except Exception as e:
        print(f"{RED}🔴 Exception occurred during audit: {e}{NC}")
        audit_failed = True
    finally:
        if server_process is not None:
            server_process.terminate()
            server_process.wait()

    return not audit_failed


# --- Verification Logic for David Evolution ---
async def run_david_verification():
    print(f"\n{CYAN}=========================================================={NC}")
    print(f"{CYAN}🚀 [David] Evolution Verification{NC}")
    print(f"{CYAN}=========================================================={NC}")
    
    import httpx
    server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
    is_docker = os.getenv("DOCKER_CONTAINER") == "true" or os.path.exists("/.dockerenv")
    server_host = "archon-server" if is_docker else "localhost"
    base_url = f"http://{server_host}:{server_port}/internal/david"
    
    try:
        async with httpx.AsyncClient() as client:
            print("🔍 Testing David's READ capability...")
            read_res = await client.get(f"{base_url}/read?path=python/src/server/main.py", timeout=5.0)
            if read_res.status_code == 200:
                print(f"  {GREEN}✅ READ Success{NC}")
            else:
                print(f"  {RED}❌ READ Failed: {read_res.status_code}{NC}")
                return False

            print("💡 Testing David's PROPOSE capability...")
            payload = {
                "file_path": "python/scratch/david_test.txt",
                "new_content": "David was here at 123456789",
                "summary": "David's sanity check proposal"
            }
            propose_res = await client.post(f"{base_url}/propose", json=payload, timeout=5.0)
            if propose_res.status_code == 200:
                print(f"  {GREEN}✅ PROPOSE Success{NC}")
                return True
            else:
                print(f"  {RED}❌ PROPOSE Failed: {propose_res.status_code}{NC}")
                return False
    except Exception as e:
        print(f"  {RED}❌ Exception occurred connecting to server: {e}{NC}")
        return False


# --- Verification Logic for Librarian ---
async def run_librarian_verification():
    print(f"\n{CYAN}=========================================================={NC}")
    print(f"{CYAN}🚀 [Librarian] Hunter Mode Verification{NC}")
    print(f"{CYAN}=========================================================={NC}")
    
    try:
        from src.agents.workflow_engine import LibrarianNode, SharedState
        state = SharedState(messages=[{"role": "user", "content": "Tell me what's the latest version of Python mentioned at https://www.python.org/downloads/"}])
        node = LibrarianNode()
        
        class MockContext:
            def __init__(self, state):
                self.state = state
        
        ctx = MockContext(state)
        print("🔍 Asking Librarian to hunt for info at python.org...")
        await node.run(ctx)
        
        last_msg = state.messages[-1]
        print(f"  {GREEN}✅ Librarian Response received{NC}")
        return True
    except Exception as e:
        print(f"  {RED}❌ Exception occurred: {e}{NC}")
        return False


async def async_main(check_type):
    success = True
    if check_type == "migrations":
        success = run_migrations_verification()
    elif check_type == "mcp":
        success = run_mcp_verification()
    elif check_type == "evolution":
        success = await run_david_verification()
    elif check_type == "librarian":
        success = await run_librarian_verification()
    elif check_type == "all":
        results = {}
        results["migrations"] = run_migrations_verification()
        results["mcp"] = run_mcp_verification()
        results["evolution"] = await run_david_verification()
        results["librarian"] = await run_librarian_verification()
        
        print(f"\n{CYAN}=========================================================={NC}")
        print(f"{CYAN}📊 Verification Summary{NC}")
        print(f"{CYAN}=========================================================={NC}")
        for k, v in results.items():
            status = f"{GREEN}PASS{NC}" if v else f"{RED}FAIL{NC}"
            print(f"  - {k:<15}: {status}")
            if not v:
                success = False
    return success

def main():
    parser = argparse.ArgumentParser(description="Archon System Verification Tool")
    parser.add_argument("--check", choices=["migrations", "mcp", "evolution", "librarian", "all"], default="all")
    args = parser.parse_args()

    # Pre-setup keys for Librarian if needed
    if os.getenv("GOOGLE_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    os.environ["WORKER_AGENT_MODEL"] = os.getenv("WORKER_AGENT_MODEL", "gemini-3.1-flash-lite")

    success = asyncio.run(async_main(args.check))
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
