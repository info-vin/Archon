import os
import subprocess
import requests
import sys

def print_header(title):
    print(f"\n{'='*20} {title} {'='*20}")

def scan_prps():
    print_header("Step 1: Scanning PRPs for pending tasks")
    prp_dir = "PRPs"
    if not os.path.exists(prp_dir):
        print(f"❌ PRPs directory '{prp_dir}' not found.")
        return
    
    pending_tasks = []
    for entry in os.listdir(prp_dir):
        full_path = os.path.join(prp_dir, entry)
        if os.path.isfile(full_path) and entry.endswith(".md"):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if "- [ ]" in line:
                        pending_tasks.append((entry, line_num, line.strip()))
                        
    if pending_tasks:
        print(f"⚠️  Found {len(pending_tasks)} pending tasks:")
        for file, line_num, content in pending_tasks:
            print(f"   - {file}:{line_num}: {content}")
    else:
        print("✅ No pending tasks found in active PRPs!")

def git_sync_check():
    print_header("Step 3: Git Sync & Tech Debt Scan")
    try:
        print("🔗 Fetching from origin...")
        subprocess.run(["git", "fetch", "origin"], check=True)
        
        print("🔍 Checking status...")
        res = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, check=True)
        if res.stdout.strip():
            print("⚠️  Working directory has changes:")
            print(res.stdout.strip())
        else:
            print("✅ Working directory clean.")
            
        print("📝 Last 5 commits:")
        subprocess.run(["git", "--no-pager", "log", "-n", "5", "--oneline"], check=True)
        
    except Exception as e:
        print(f"❌ Git check failed: {e}")

def monolith_check():
    print_header("Monolith Check (> 400 lines & Warnings > 360 lines)")
    target_dirs = ["python/src", "enduser-ui-fe/src", "archon-ui-main/src"]
    large_files = []
    warning_files = []
    
    for base_dir in target_dirs:
        if not os.path.exists(base_dir): continue
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith((".py", ".ts", ".tsx")) and not any(x in root for x in ["tests", "__tests__", "node_modules"]):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = sum(1 for _ in f)
                        if lines > 400:
                            large_files.append((file_path, lines))
                        elif lines > 360:
                            warning_files.append((file_path, lines))
                    except: pass
                        
    def print_separated(files_list, label_icon, label_text):
        if not files_list:
            return False
            
        backend_files = [x for x in files_list if x[0].startswith("python/")]
        frontend_files = [x for x in files_list if not x[0].startswith("python/")]
        
        print(f"{label_icon} Found {len(files_list)} {label_text}:")
        
        if backend_files:
            print("   [Backend]")
            for path, count in sorted(backend_files, key=lambda x: x[1], reverse=True):
                print(f"     - {path}: {count} lines")
        if frontend_files:
            print("   [Frontend]")
            for path, count in sorted(frontend_files, key=lambda x: x[1], reverse=True):
                print(f"     - {path}: {count} lines")
        return True
                        
    has_large = print_separated(large_files, "❌", "monoliths (>400 lines)")
    if not has_large:
        print("✅ No monolith files (>400 lines) found!")
        
    print_separated(warning_files, "⚠️ ", "files nearing monolith status (>360 lines)")

def cloud_audit():
    print_header("Step 5: Cloud & Scheduler Audit (Hugging Face)")
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("ℹ️  HF_TOKEN not set, skipping Cloud Audit.")
        return
        
    username = "chiawei6"
    space_name = "myrmidon"
    url = f"https://huggingface.co/api/spaces/{username}/{space_name}"
    
    try:
        headers = {"Authorization": f"Bearer {hf_token}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        runtime = data.get("runtime", {})
        stage = runtime.get("stage", "UNKNOWN")
        print(f"✅ Space {username}/{space_name} is currently: {stage}")
        
        if stage != "RUNNING":
            print(f"⚠️  Space is not RUNNING! Current status: {stage}")
            
    except Exception as e:
        print(f"❌ Cloud audit failed: {e}")

def architecture_health_audit():
    print_header("Step 6: Four Major Backend Architectures Health Check")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from backend_type_health import generate_health_report_markdown
        print(generate_health_report_markdown())
    except Exception as e:
        print(f"❌ Architecture health audit failed: {e}")

def schema_sync_audit():
    import re
    print_header("Step 7: Physical Schema Three-Way Sync Audit")
    
    # 1. Parse all sql files in migration/ for tables and views
    sql_tables = set()
    migration_dir = "migration"
    if os.path.exists(migration_dir):
        for root, _, files in os.walk(migration_dir):
            for file in files:
                if file.endswith(".sql"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        # Match CREATE TABLE
                        t_matches = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[\w]+\.)?[\"']?([a-zA-Z0-9_]+)[\"']?", content, re.IGNORECASE)
                        sql_tables.update(t_matches)
                        
                        # Match CREATE VIEW
                        v_matches = re.findall(r"CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:[\w]+\.)?[\"']?([a-zA-Z0-9_]+)[\"']?", content, re.IGNORECASE)
                        sql_tables.update(v_matches)
                        
                        # Match ALTER TABLE RENAME TO
                        r_matches = re.findall(r"ALTER\s+TABLE\s+(?:[\w]+\.)?[\"']?[a-zA-Z0-9_]+[\"']?\s+RENAME\s+TO\s+(?:[\w]+\.)?[\"']?([a-zA-Z0-9_]+)[\"']?", content, re.IGNORECASE)
                        sql_tables.update(r_matches)
                        
    # Supabase system tables we might query
    sql_tables.update({"auth.users", "schema_migrations", "pg_stat_activity", "archon_migrations"})
                        
    # 2. Parse python/src for .table("...")
    python_dir = "python/src"
    python_tables = set()
    ghost_tables = set()
    
    if os.path.exists(python_dir):
        for root, _, files in os.walk(python_dir):
            for file in files:
                if file.endswith(".py") and not any(x in root for x in ["tests", "__tests__"]):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = re.findall(r"\.table\([\"']([a-zA-Z0-9_]+)[\"']\)", content)
                        python_tables.update(matches)
                        
    for pt in python_tables:
        if pt not in sql_tables:
            ghost_tables.add(pt)
            
    if ghost_tables:
        print(f"❌ FOUND GHOST TABLES IN PYTHON CODE: {ghost_tables}")
        print("These tables are queried via .table() in Python but are NOT created in migration SQL!")
        sys.exit(1)
    else:
        print("✅ Schema sync audit passed. No ghost tables found.")

def ssot_hardcoding_audit():
    import re
    print_header("Step 8: SSOT & Hardcoding Audit")
    
    target_dirs = ["python/src/server/services", "python/src/server/api_routes"]
    hardcoded_issues = []
    
    # 掃描 asyncio.sleep(數字) 與寫死的 http://... 網址
    sleep_pattern = re.compile(r"asyncio\.sleep\(\s*([0-9\.]+)\s*\)")
    url_pattern = re.compile(r"[\"']https?://[a-zA-Z0-9_\-\.]+:\d+[\"']")
    cron_pattern = re.compile(r"CronTrigger\([^)]*(hour=\d+|minute=\d+|day_of_week=[\"'][a-zA-Z,]+[\"'])[^)]*\)")
    # 新增：偵測寫死的字串集合 (例如 {"delete_project", "execute_sql"})
    set_literal_pattern = re.compile(r"\{\s*[\"'][a-zA-Z0-9_]+[\"']\s*(?:,\s*[\"'][a-zA-Z0-9_]+[\"']\s*)+\}")
    
    for base_dir in target_dirs:
        if not os.path.exists(base_dir): continue
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".py") and not any(x in root for x in ["tests", "__tests__"]):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if line.strip().startswith("#"): continue
                            
                            sleep_match = sleep_pattern.search(line)
                            if sleep_match:
                                try:
                                    if float(sleep_match.group(1)) >= 1.0:
                                        hardcoded_issues.append((file_path, line_num, "Hardcoded asyncio.sleep()", line.strip()))
                                except ValueError:
                                    pass
                            elif url_pattern.search(line):
                                hardcoded_issues.append((file_path, line_num, "Hardcoded HTTP URL/Port", line.strip()))
                            elif cron_pattern.search(line):
                                hardcoded_issues.append((file_path, line_num, "Hardcoded CronTrigger rules", line.strip()))
                            elif set_literal_pattern.search(line):
                                hardcoded_issues.append((file_path, line_num, "Hardcoded String Set Literal (SSOT Violation)", line.strip()))
                                
    if hardcoded_issues:
        print(f"⚠️  Found {len(hardcoded_issues)} potential hardcoding / SSOT violations:")
        for path, line_num, issue, content in hardcoded_issues:
            # 限制長度避免洗頻
            short_content = content if len(content) < 80 else content[:77] + "..."
            print(f"   - {path}:{line_num} | {issue} | {short_content}")
    else:
        print("✅ SSOT & Hardcoding audit passed. No obvious magic numbers found.")

if __name__ == "__main__":
    scan_prps()
    git_sync_check()
    monolith_check()
    cloud_audit()
    architecture_health_audit()
    schema_sync_audit()
    ssot_hardcoding_audit()
    print_header("Audit Complete")

