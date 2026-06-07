import os
import re
import subprocess
import sys

def scan_prps():
    print("📋 [PhaseAudit] Step 1: Scanning PRPs for pending tasks...")
    prp_dir = "PRPs"
    if not os.path.exists(prp_dir):
        print(f"❌ PRPs directory '{prp_dir}' not found.")
        return
    
    pending_tasks = []
    # Only scan markdown files directly in PRPs/
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

def check_git_status():
    print("\n🌿 [PhaseAudit] Step 2: Checking Git Status...")
    try:
        res = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, check=True)
        status_output = res.stdout.strip()
        if status_output:
            print("⚠️  Working directory has uncommitted or untracked changes:")
            print(status_output)
        else:
            print("✅ Working directory is clean!")
    except Exception as e:
        print(f"❌ Failed to run git status: {e}")

def monolith_check():
    print("\n🔍 [PhaseAudit] Step 3: Running Monolith Check (Files > 400 lines)...")
    target_dirs = ["python/src", "enduser-ui-fe/src", "archon-ui-main/src"]
    large_files = []
    
    for base_dir in target_dirs:
        if not os.path.exists(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            # Avoid node_modules or other hidden directories if any
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            for file in files:
                if file.endswith((".py", ".ts", ".tsx")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = sum(1 for _ in f)
                        if lines > 400:
                            large_files.append((file_path, lines))
                    except Exception:
                        pass
                        
    if large_files:
        print(f"⚠️  Found {len(large_files)} files exceeding 400 lines (potential monoliths):")
        # Sort by line count descending
        large_files.sort(key=lambda x: x[1], reverse=True)
        for path, count in large_files:
            print(f"   - {path}: {count} lines")
    else:
        print("✅ No monolith files (> 400 lines) found!")

if __name__ == "__main__":
    scan_prps()
    check_git_status()
    monolith_check()
