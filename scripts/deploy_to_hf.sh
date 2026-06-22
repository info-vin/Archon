#!/usr/bin/env bash
# scripts/deploy_to_hf.sh
# Automates the Hugging Face Spaces deployment using a clean orphan branch to bypass file size limits.

set -e

# Configuration
SOURCE_BRANCH=$(git branch --show-current)
TEMP_BRANCH="deploy-hf"
REMOTE_NAME="hf"

echo "=== Hugging Face Spaces Auto-Deployer ==="
echo "Current branch: $SOURCE_BRANCH"

# Check if hf remote exists
if ! git remote | grep -q "^$REMOTE_NAME$"; then
  echo "Error: Git remote '$REMOTE_NAME' not found."
  echo "Please add it first using:"
  echo "  git remote add hf https://huggingface.co/spaces/<username>/<space_name>"
  exit 1
fi

# Ensure workspace doesn't have uncommitted changes
if ! git diff-index --quiet HEAD --; then
  echo "Warning: You have uncommitted changes. Please stash or commit them before deploying."
  read -p "Do you want to proceed anyway? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Ensure we clean up if anything fails
cleanup() {
  echo "Cleaning up temp branch and files..."
  git checkout -f "$SOURCE_BRANCH" 2>/dev/null || true
  git branch -D "$TEMP_BRANCH" 2>/dev/null || true
  echo "Cleanup complete."
}
trap cleanup ERR EXIT

echo "1. Creating clean orphan branch '$TEMP_BRANCH'..."
git checkout --orphan "$TEMP_BRANCH"

echo "2. Clearing staging area..."
git rm -rf . > /dev/null

echo "3. Restoring required backend directories/files from $SOURCE_BRANCH..."
git checkout "$SOURCE_BRANCH" -- python/
git checkout "$SOURCE_BRANCH" -- migration/
git checkout "$SOURCE_BRANCH" -- scripts/
git checkout "$SOURCE_BRANCH" -- Makefile
git checkout "$SOURCE_BRANCH" -- Dockerfile.server

echo "3.5 Removing binary artifacts to comply with HF limits..."
git rm -rf --cached python/.twin/ 2>/dev/null || true
rm -rf python/.twin/


echo "4. Copying Dockerfile.server to root Dockerfile..."
cp Dockerfile.server Dockerfile

echo "5. Generating metadata README.md..."
cat << 'EOF' > README.md
---
title: Myrmidon
emoji: 🐳
colorFrom: blue
colorTo: pink
sdk: docker
app_port: 8181
pinned: false
---
# Myrmidon Backend
EOF

echo "6. Adding files to index and committing..."
git add python/ migration/ scripts/ Makefile Dockerfile README.md
git commit -m "chore(deploy): build monolithic server for Hugging Face"

echo "7. Pushing to Hugging Face Spaces (main branch)..."
git push hf "$TEMP_BRANCH:main" --force

echo "🎉 Deployment successfully pushed to Hugging Face Spaces!"
