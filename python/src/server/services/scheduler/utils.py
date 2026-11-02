"""
Shared DRY & SSOT utilities for Scheduler Jobs and Agent Task Routing.
"""

from pathlib import Path
from typing import Any

from src.server.config.logfire_config import get_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.schemas.settings import ProjectConfig
from src.server.services.settings_service import SettingsService
from src.server.services.shared_constants import AI_AGENT_ROLES
from src.server.utils import get_supabase_client

logger = get_logger(__name__)


def resolve_project_root(marker_rel_path: str = "scripts/backend_type_health.py") -> Path:
    """
    Multi-path detection (Host vs Docker) for finding project root files.
    """
    possible_roots = [
        Path.cwd(),
        Path.cwd().parent,
        Path("/app"),
        Path(__file__).resolve().parents[5],
        Path(__file__).resolve().parents[4],
    ]
    for root in possible_roots:
        if (root / marker_rel_path).exists():
            return root
    return Path.cwd() if Path.cwd().exists() else Path("/app")


def get_default_project_id(supabase: Any = None, error_context: str = "Get default project ID") -> str | None:
    """
    SSOT/DRY helper to resolve the active default project ID from ProjectConfig or fallback to archon_projects.
    """
    client = supabase or get_supabase_client()
    try:
        settings = SettingsService(client)
        config = ProjectConfig.model_validate(settings.get_all_settings())
        if config.default_business_project:
            return config.default_business_project
    except Exception:
        pass

    repo = BaseRepository(client)
    success, res = repo.execute_query(
        client.table("archon_projects").select("id").limit(1),
        error_context,
    )
    if success and isinstance(res.get("data"), list) and len(res["data"]) > 0:
        first_row = res["data"][0]
        if isinstance(first_row, dict) and first_row.get("id"):
            return str(first_row["id"])
    return None


def normalize_agent_identity(agent_id_or_name: str | None) -> tuple[str, str]:
    """
    Resolves any agent UUID or display name to (canonical_uuid, display_name) using AI_AGENT_ROLES SSOT.
    If not an AI agent in AI_AGENT_ROLES, returns (str(agent_id_or_name), str(agent_id_or_name)).
    """
    if not agent_id_or_name:
        return "", ""

    raw = str(agent_id_or_name).strip()
    for role_name, role_uuid in AI_AGENT_ROLES.items():
        if raw == role_uuid or raw == role_name:
            return role_uuid, role_name

    for role_name, role_uuid in AI_AGENT_ROLES.items():
        if role_name.startswith(raw) or raw in role_name:
            return role_uuid, role_name

    return raw, raw
