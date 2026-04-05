"""
Version configuration for Archon.
"""

import logging
import os

logger = logging.getLogger(__name__)

def get_latest_version() -> str:
    """
    Dynamically detects the latest version from the migration directory.
    Standardizes on the folder name (e.g., 0.2.2).
    """
    try:
        # Physical Search Strategy: Try multiple common root paths
        # 1. /app/migration (Docker)
        # 2. ../../../../migration (Local src/server/config)
        # 3. migration (Local root)
        possible_paths = [
            "/app/migration",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "migration")),
            os.path.abspath(os.path.join(os.getcwd(), "migration")),
            "migration"
        ]
        
        base_path = None
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                base_path = path
                break
        
        if not base_path:
            return os.getenv("ARCHON_VERSION", "0.2.1")

        subdirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and d[0].isdigit()]
        if not subdirs:
            return os.getenv("ARCHON_VERSION", "0.2.1")

        # Sort by version components to handle 0.10.0 > 0.2.0 correctly
        latest = sorted(subdirs, key=lambda x: [int(c) for d in [x.split('.')] for c in d])[-1]
        return latest
    except Exception as e:
        logger.warning(f"Failed to detect dynamic version: {e}")
        return os.getenv("ARCHON_VERSION", "0.2.1")

# Current version of Archon - Dynamically detected
ARCHON_VERSION = get_latest_version()

# Repository information for GitHub API
GITHUB_REPO_OWNER = "coleam00"
GITHUB_REPO_NAME = "Archon"

