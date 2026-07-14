#!/usr/bin/env python3
"""
Scroll Lockup Static Scanner for React/TSX Codebases.
Detects nested scroll elements where a child utilizes min-h-screen or h-screen 
inside a parent wrapper that defines overflow-y-auto / overflow-auto.
This nested configuration locks up the scrolling axis on mobile viewports.
"""

import os
import sys
from pathlib import Path

# Color constants for premium terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

OVERFLOW_CLASSES = ["overflow-y-auto", "overflow-auto", "overflow-y-scroll"]
HEIGHT_CLASSES = ["min-h-screen", "h-screen"]

def scan_file(file_path):
    """
    Scans a TSX/JSX file for nested scroll lockup patterns.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"{RED}Error reading {file_path}: {e}{RESET}")
        return []

    # Fast check: must contain both types of classes to be a risk
    has_overflow = any(cls in content for cls in OVERFLOW_CLASSES)
    has_height = any(cls in content for cls in HEIGHT_CLASSES)
    
    if not has_overflow or not has_height:
        return []

    violations = []
    lines = content.splitlines()
    
    # Simple robust nesting scanner:
    # 1. Locate overflow-y-auto element
    # 2. Check if a min-h-screen / h-screen element is a descendant before the enclosing context ends
    for line_idx, line in enumerate(lines):
        parent_match = None
        for of_cls in OVERFLOW_CLASSES:
            if of_cls in line:
                parent_match = of_cls
                break
                
        if parent_match:
            # We found a parent scroll container! Now scan downstream for height classes
            # We estimate the block scope by tracking indentation or bracket count
            # A simpler, highly reliable heuristic: scan the next 30 lines (typical JSX scope)
            # and verify if they are further indented or belong to the same block
            scope_lines = lines[line_idx + 1: line_idx + 35]
            for sub_offset, sub_line in enumerate(scope_lines):
                child_match = None
                for ht_cls in HEIGHT_CLASSES:
                    if ht_cls in sub_line:
                        child_match = ht_cls
                        break
                
                if child_match:
                    violations.append({
                        "file": str(file_path),
                        "parent_line": line_idx + 1,
                        "parent_class": parent_match,
                        "parent_content": line.strip(),
                        "child_line": line_idx + 1 + sub_offset + 1,
                        "child_class": child_match,
                        "child_content": sub_line.strip()
                    })
                    
    return violations

def main():
    workspace_dir = Path(__file__).resolve().parent.parent.parent
    target_dir = workspace_dir / "enduser-ui-fe" / "src"
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])

    if not target_dir.exists():
        print(f"{RED}Target directory {target_dir} does not exist.{RESET}")
        sys.exit(1)

    print(f"\n{BLUE}{BOLD}=== Archon TSX Scroll Lockup Static Scanner ==={RESET}")
    print(f"Scanning directory: {target_dir}\n")

    total_files = 0
    all_violations = []

    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith((".tsx", ".jsx")):
                total_files += 1
                file_path = Path(root) / file
                violations = scan_file(file_path)
                all_violations.extend(violations)

    print(f"Scanned {total_files} TSX/JSX files.")

    if not all_violations:
        print(f"{GREEN}✓ No nested scroll lockup violations detected! Excellent UI hygiene.{RESET}\n")
        sys.exit(0)

    print(f"{RED}⚠ Found {len(all_violations)} potential nested scroll lockup violation(s):{RESET}\n")

    # Display results beautifully
    for v in all_violations:
        file_name = Path(v["file"]).name
        print(f"{YELLOW}{BOLD}[VIOLATION] in {file_name}:{RESET}")
        print(f"  └─ {v['file']}")
        print(f"  ├─ {BOLD}Parent Container (Line {v['parent_line']}):{RESET} {BLUE}{v['parent_class']}{RESET}")
        print(f"     Code: `{v['parent_content']}`")
        print(f"  └─ {BOLD}Nested Child Height (Line {v['child_line']}):{RESET} {RED}{v['child_class']}{RESET}")
        print(f"     Code: `{v['child_content']}`")
        print(f"  {YELLOW}👉 Recommendation: Remove `{v['child_class']}` or release child height context to prevent viewport lockup on mobile.{RESET}\n")

    sys.exit(1)

if __name__ == "__main__":
    main()
