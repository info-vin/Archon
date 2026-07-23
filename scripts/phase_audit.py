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
        subprocess.run(["git", "log", "-n", "5", "--oneline"], check=True)
        
    except Exception as e:
        print(f"❌ Git check failed: {e}")

def monolith_check():
    print_header("Monolith Check (> 400 lines)")
    target_dirs = ["python/src", "enduser-ui-fe/src", "archon-ui-main/src"]
    large_files = []
    
    for base_dir in target_dirs:
        if not os.path.exists(base_dir): continue
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith((".py", ".ts", ".tsx")) and not any(x in root for x in ["tests", "__tests__", "node_modules"]):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = sum(1 for _ in f)
                        if lines > 400: large_files.append((file_path, lines))
                    except: pass
                        
    if large_files:
        print(f"⚠️  Found {len(large_files)} monoliths:")
        for path, count in sorted(large_files, key=lambda x: x[1], reverse=True):
            print(f"   - {path}: {count} lines")
    else:
        print("✅ No monolith files found!")

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


if __name__ == "__main__":
    scan_prps()
    git_sync_check()
    monolith_check()
    cloud_audit()
    architecture_health_audit()
    print_header("Audit Complete")

