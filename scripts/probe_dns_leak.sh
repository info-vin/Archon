#!/usr/bin/env bash
# scripts/probe_dns_leak.sh
# Phase 5.2.0 Task 5.2.0.2: Frontend DNS & API Leak Probe
# This script scans compiled static assets in dist/ directories to detect internal Docker DNS or local APIs.

set -euo pipefail

# ANSI color codes for premium Tron-inspired output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}==========================================================${NC}"
echo -e "${CYAN}🔍 Phase 5.2.0: Frontend DNS & API Leak Probe${NC}"
echo -e "${CYAN}==========================================================${NC}"

# Directories to scan (defaults to checking both frontends)
DEFAULT_DIRS=("enduser-ui-fe/dist" "archon-ui-main/dist")
DIRS_TO_SCAN=()

if [ $# -gt 0 ]; then
    DIRS_TO_SCAN=("$@")
else
    DIRS_TO_SCAN=("${DEFAULT_DIRS[@]}")
fi

# Define regex patterns for critical internal network structures
# 1. _kong (Supabase internal gateway)
# 2. localhost:8000 (Default API server)
# 3. localhost:8181 (Backend service port)
# 4. localhost:8051 (MCP service port)
# 5. Docker private IPs (172.16.x.x to 172.31.x.x, or general 172.x subnets with word boundaries)
PATTERNS=(
    "_kong"
    "localhost:8000"
    "localhost:8181"
    "localhost:8051"
    "\\b172\\.(1[6-9]|2[0-9]|3[0-1])\\.[0-9]+\\.[0-9]+\\b"
)

LEAK_FOUND=0
SCANNED_COUNT=0
TOTAL_FILES=0

# Create a temporary file to collect audit logs safely
TEMP_MATCH_FILE=$(mktemp)

for dir in "${DIRS_TO_SCAN[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}⚠️  Warning: Directory '$dir' does not exist. Skipping...${NC}"
        continue
    fi

    echo -e "${BLUE}Scanning compiled static assets in '$dir'...${NC}"
    
    # Locate all text-based static assets (HTML, JS, CSS, JSON, SVG)
    while IFS= read -r file; do
        TOTAL_FILES=$((TOTAL_FILES + 1))
        
        for pattern in "${PATTERNS[@]}"; do
            # Scan file with case-insensitive extended regex
            # Filter out the legitimate proactive guard check for '_kong' in JS files
            if grep -E -n -i "$pattern" "$file" | grep -v -E 'includes\(["'\'']_kong["'\'']\)' > "$TEMP_MATCH_FILE"; then
                if [ -s "$TEMP_MATCH_FILE" ]; then
                    echo -e "${RED}❌ LEAK DETECTED in $file!${NC}"
                    echo -e "${YELLOW}Matched Pattern: '$pattern'${NC}"
                    while IFS= read -r line; do
                        echo -e "  ${RED}Line $line${NC}"
                    done < "$TEMP_MATCH_FILE"
                    LEAK_FOUND=1
                fi
            fi
        done
        SCANNED_COUNT=$((SCANNED_COUNT + 1))
    done < <(find "$dir" -type f \( -name "*.html" -o -name "*.js" -o -name "*.css" -o -name "*.json" -o -name "*.svg" \) -not -path '*/.*' -not -path '*/test-results/*' -not -path '*/coverage/*')
done

rm -f "$TEMP_MATCH_FILE"

echo -e "${CYAN}----------------------------------------------------------${NC}"
echo -e "Total scanned files: $TOTAL_FILES"

if [ "$SCANNED_COUNT" -eq 0 ]; then
    echo -e "${RED}🚨 Error: No static files were scanned. Make sure you build the frontends first!${NC}"
    exit 1
fi

if [ "$LEAK_FOUND" -eq 0 ]; then
    echo -e "${GREEN}🟢 [SUCCESS] DNS Leak Probe passed! No internal domains or IPs leaked in static assets.${NC}"
    exit 0
else
    echo -e "${RED}🔴 [FAILURE] DNS Leak Probe failed! Internal configurations leaked in compiled files.${NC}"
    exit 1
fi
