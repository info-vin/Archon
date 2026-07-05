#!/usr/bin/env python3
import os
import sys
import re

# ANSI color codes for premium Tron-inspired output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def main():
    print(f"{CYAN}=========================================================={NC}")
    print(f"{CYAN}🔍 Phase 5.2.0: Frontend DNS & API Leak Probe (Python Version){NC}")
    print(f"{CYAN}=========================================================={NC}")

    from pathlib import Path
    workspace_dir = Path(__file__).resolve().parent.parent

    default_dirs = ["enduser-ui-fe/dist", "archon-ui-main/dist"]
    dirs_to_scan = sys.argv[1:] if len(sys.argv) > 1 else default_dirs

    # Resolve paths relative to workspace_dir if not absolute
    resolved_dirs = []
    for d in dirs_to_scan:
        if os.path.isabs(d):
            resolved_dirs.append(d)
        else:
            resolved_dirs.append(os.path.join(workspace_dir, d))

    patterns = [
        re.compile(r"_kong", re.IGNORECASE),
        re.compile(r"localhost:8000", re.IGNORECASE),
        re.compile(r"localhost:8181", re.IGNORECASE),
        re.compile(r"localhost:8051", re.IGNORECASE),
        re.compile(r"\b172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]+\.[0-9]+\b")
    ]

    leak_found = False
    scanned_count = 0
    total_files = 0

    for scan_dir in resolved_dirs:
        if not os.path.isdir(scan_dir):
            print(f"{YELLOW}⚠️  Warning: Directory '{scan_dir}' does not exist. Skipping...{NC}")
            continue

        print(f"{BLUE}Scanning compiled static assets in '{scan_dir}'...{NC}")

        for root, dirs, files in os.walk(scan_dir):
            # Exclude hidden, test-results, and coverage folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'test-results', 'coverage'}]
            
            for file in files:
                if file.endswith((".html", ".js", ".css", ".json", ".svg")):
                    filepath = os.path.join(root, file)
                    total_files += 1
                    scanned_count += 1
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                        
                        for line_num, line in enumerate(lines, 1):
                            for pattern in patterns:
                                # Search for the pattern
                                if pattern.search(line):
                                    # Filter out legitimate proactive guard checks for '_kong' in JS files
                                    if "_kong" in pattern.pattern and ("includes('_kong')" in line or 'includes("_kong")' in line):
                                        continue
                                    
                                    print(f"{RED}❌ LEAK DETECTED in {filepath}!{NC}")
                                    print(f"{YELLOW}Matched Pattern: '{pattern.pattern}'{NC}")
                                    print(f"  {RED}Line {line_num}: {line.strip()[:100]}{NC}")
                                    leak_found = True
                    except Exception as e:
                        print(f"{YELLOW}⚠️  Unable to read file {filepath}: {e}{NC}")

    print(f"{CYAN}----------------------------------------------------------{NC}")
    print(f"Total scanned files: {total_files}")

    if scanned_count == 0:
        print(f"{RED}🚨 Error: No static files were scanned. Make sure you build the frontends first!{NC}")
        sys.exit(1)

    if not leak_found:
        print(f"{GREEN}🟢 [SUCCESS] DNS Leak Probe passed! No internal domains or IPs leaked in static assets.{NC}")
        sys.exit(0)
    else:
        print(f"{RED}🔴 [FAILURE] DNS Leak Probe failed! Internal configurations leaked in compiled files.{NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
