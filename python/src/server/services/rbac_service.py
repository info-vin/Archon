# python/src/server/services/rbac_service.py

from typing import Any, cast

from src.server.repositories.base_repository import BaseRepository

from ..auth.permissions import ROLE_PERMISSIONS
from ..config.logfire_config import get_logger
from ..models.auth_models import UserProfileDTO
from ..utils import get_supabase_client

logger = get_logger(__name__)


class RBACService(BaseRepository):
    """
    Service for handling Role-Based Access Control (RBAC) logic.
    Phase 4.6.31: Transitioned from hardcoded dicts to dynamic database-backed matrix.
    """

    _matrix_cache: dict[str, set[str]] | None = None

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client or get_supabase_client())
        # Initial assignment rules (Static fallback)
        self.permissions = {
            "admin": ["admin", "system_admin", "manager", "employee", "member", "marketing", "sales", "ai_agent"],
            "system_admin": [
                "admin",
                "system_admin",
                "manager",
                "employee",
                "member",
                "marketing",
                "sales",
                "ai_agent",
            ],
            "manager": ["manager", "employee", "member", "marketing", "sales", "ai_agent"],
            "employee": ["employee", "member", "ai_agent"],
            "member": ["employee", "member", "ai_agent"],
            "marketing": ["marketing", "ai_agent"],
            "sales": ["sales", "ai_agent"],
            "pm": ["manager", "employee", "member", "marketing", "sales", "ai_agent"],
            "engineer": ["employee", "member", "ai_agent"],
        }

    async def get_role_permissions(self, role: str) -> set[str]:
        """
        Returns the set of permissions for a given role.
        Priority: 1. DB (Dynamic) -> 2. permissions.py (Static Fallback)
        """
        matrix = await self.get_matrix()
        return matrix.get(role.lower(), set())

    async def get_matrix(self, force_refresh: bool = False) -> dict[str, set[str]]:
        """Retrieves the full role-permission matrix, with caching support."""
        if not force_refresh and self._matrix_cache is not None:
            return self._matrix_cache

        # Try to load from Database
        query = self.supabase_client.table("archon_roles_permissions").select("role, permissions")
        success, result = self.execute_query(query, "Failed to load dynamic RBAC matrix from DB", require_data=False)

        if success and result.get("data"):
            dynamic_matrix = {item["role"].lower(): set(item["permissions"]) for item in result["data"]}
            RBACService._matrix_cache = dynamic_matrix
            logger.info(f"Loaded {len(dynamic_matrix)} roles from dynamic RBAC matrix")
            return dynamic_matrix

        logger.warning("Failed to load dynamic RBAC matrix from DB or no data, falling back to static")

        # Fallback to static permissions.py
        static_matrix = {role.lower(): perms for role, perms in ROLE_PERMISSIONS.items()}
        RBACService._matrix_cache = static_matrix
        return static_matrix

    def get_crawler_constraints(self, current_user_role: str | None) -> dict:
        """
        Retrieves crawler constraints (max depth, concurrent) for a specific role
        from archon_settings.
        """
        role = (current_user_role or "member").lower()

        # Mapping simple roles to their settings suffix
        role_map = {
            "admin": "ADMIN",
            "system_admin": "ADMIN",
            "manager": "MANAGER",
            "marketing": "MARKETING",
            "sales": "SALES",
        }
        suffix = role_map.get(role, "SALES")  # Default to strictest (SALES) for unknown roles

        # Default safe values if DB fetch fails
        constraints = {
            "max_depth": 2,
            "max_concurrent": 3,
            "allowed_domains": ["104.com.tw", "github.com", "google.com"],
        }

        try:
            # 1. Fetch static settings from archon_settings
            keys = [f"CRAWL_MAX_DEPTH_{suffix}", f"CRAWL_CONCURRENT_MAX_{suffix}", "CRAWL_ALLOWED_DOMAINS_RESTRICTED"]
            query = self.supabase_client.table("archon_settings").select("key, value").in_("key", keys)
            success, result = self.execute_query(query, "Failed to fetch settings", require_data=False)

            if success and result.get("data"):
                settings = {item["key"]: item["value"] for item in result["data"]}

                depth_key = f"CRAWL_MAX_DEPTH_{suffix}"
                if depth_key in settings:
                    constraints["max_depth"] = int(settings[depth_key])

                concurrent_key = f"CRAWL_CONCURRENT_MAX_{suffix}"
                if concurrent_key in settings:
                    constraints["max_concurrent"] = int(settings[concurrent_key])

                if "CRAWL_ALLOWED_DOMAINS_RESTRICTED" in settings:
                    domains = settings["CRAWL_ALLOWED_DOMAINS_RESTRICTED"].split(",")
                    constraints["allowed_domains"] = [d.strip() for d in domains if d.strip()]

            # 2. 物理加固：從 archon_crawler_targets 動態抓取 David 在 3737 設定的白名單
            # 這實現了 David 在 3737 設定 URL 與後端爬蟲權限的物理連動
            dynamic_query = (
                self.supabase_client.table("archon_crawler_targets").select("whitelist, target_url").eq("is_active", True)
            )
            d_success, dynamic_result = self.execute_query(dynamic_query, "Failed to fetch dynamic crawler targets", require_data=False)

            if d_success and dynamic_result.get("data"):
                allowed_domains = cast(list[str], constraints["allowed_domains"])

                for target in dynamic_result["data"]:
                    # 加入主網址網域 (Domain) 作為基本許可
                    from urllib.parse import urlparse

                    domain = urlparse(target["target_url"]).netloc
                    if domain and domain not in allowed_domains:
                        allowed_domains.append(domain)

                    # 加入 David 設定的詳細白名單 Patterns
                    if target.get("whitelist"):
                        for pattern in target["whitelist"]:
                            if pattern and pattern not in allowed_domains:
                                allowed_domains.append(pattern)
        except Exception as e:
            logger.error(f"Failed to fetch crawler constraints for role {role}: {e}")

        return constraints

    async def has_permission(self, user: UserProfileDTO | None, permission: str) -> bool:
        """
        Checks if a user has a specific permission.
        Args:
            user: UserProfileDTO instance
            permission: The permission scope to check (e.g. TASK_CREATE)
        """
        if not user:
            return False

        # 1. Check per-user overrides first (High priority)
        overrides = user.permission_overrides or {}
        if permission in overrides:
            return bool(overrides[permission])

        # 2. Fallback to role-based permissions
        user_role = (user.role or "viewer").lower()
        role_perms = await self.get_role_permissions(user_role)
        return permission in role_perms or user_role in ["admin", "system_admin"]

    async def has_permission_to_assign(self, current_user_role: str, assignee_role: str) -> bool:
        """Checks if the current user role has permission to assign tasks to the target role."""
        if not current_user_role or not assignee_role:
            return False

        current_role = current_user_role.lower()
        target_role = assignee_role.lower()

        # 1. Try dynamic permission matrix first
        perms = await self.get_role_permissions(current_role)
        if perms:
            if f"assign:{target_role}" in perms:
                return True
            if "assign:all" in perms or current_role in ["admin", "system_admin"]:
                return True

        # 2. Fallback to static permissions mapping
        allowed_roles = self.permissions.get(current_role, [])

        # Direct role match
        if target_role in allowed_roles:
            return True

        # Agent wildcard check
        if target_role == "ai_agent" and "ai_agent" in allowed_roles:
            return True

        return False

    async def get_assignable_roles(self, current_user_role: str) -> list[str]:
        """Returns a list of roles that the current user can assign tasks to."""
        if not current_user_role:
            return []
        current_role = current_user_role.lower()

        # 1. Try dynamic permission matrix first
        perms = await self.get_role_permissions(current_role)
        if perms:
            assignable = []
            for p in perms:
                if p.startswith("assign:"):
                    assignable.append(p.split(":")[1])
            if assignable:
                if "all" in assignable:
                    matrix = await self.get_matrix()
                    return list(matrix.keys())
                return assignable

        # 2. Fallback to static
        return self.permissions.get(current_role, [])

    def can_manage_content(self, current_user_role: str) -> bool:
        """Checks if the current user role has permission to manage content."""
        if not current_user_role:
            return False
        # Define roles that can manage content (case-insensitive)
        # Updated Phase 4.4: Sales and Marketing are content creators too.
        content_manager_roles = ["admin", "system_admin", "manager", "marketing", "sales"]
        return current_user_role.lower() in content_manager_roles

    def scope_projects(self, projects: list[dict], user: UserProfileDTO) -> list[dict]:
        """
        Filters a list of projects based on user's department and role.
        Centralized logic from projects/core.py for Phase 4.6.30.
        """
        role = (user.role or "viewer").lower()
        dept = user.department

        if role in ["system_admin", "admin"]:
            return projects

        return [p for p in projects if p.get("department") == dept or not p.get("department")]

    def validate_project_access(self, project: dict | UserProfileDTO, user: UserProfileDTO) -> bool:
        """
        Validates if a user has access to a specific project based on department.
        Centralized logic from projects/core.py for Phase 4.6.30.
        """
        role = (user.role or "viewer").lower()
        dept = user.department

        if role in ["system_admin", "admin"]:
            return True

        project_dept = getattr(project, "department", None) if not isinstance(project, dict) else project.get("department")
        if not project_dept:
            return True

        return bool(project_dept == dept)

    async def get_restricted_mcp_tools(self, role_or_agent: str) -> set[str]:
        """
        Returns a set of MCP tool names that are RESTRICTED (forbidden) for a given role or agent type.
        Phase 5.1: Dynamic MCP Tool Schema Cropping based on RBAC.
        """
        role = (role_or_agent or "anonymous").lower()

        # High-level roles have no restrictions
        if role in ["admin", "system_admin", "charlie"]:
            return set()

        # Fetch from archon_settings for dynamic restrictions
        query = self.supabase_client.table("archon_settings").select("key, value").in_("key", ["MCP_RESTRICTED_BASE", f"MCP_RESTRICTED_{role.upper()}"])
        success, result = self.execute_query(query, "Failed to fetch MCP restrictions", require_data=False)

        restricted_tools = set()

        if success and result.get("data"):
            settings = {item["key"]: item["value"] for item in result["data"]}
            if "MCP_RESTRICTED_BASE" in settings:
                restricted_tools.update([t.strip() for t in settings["MCP_RESTRICTED_BASE"].split(",") if t.strip()])

            role_key = f"MCP_RESTRICTED_{role.upper()}"
            if role_key in settings:
                restricted_tools.update([t.strip() for t in settings[role_key].split(",") if t.strip()])
        else:
            # Fallback (DB independent)
            restricted_tools = set(["delete_project", "delete_task", "run_system_command", "execute_sql"])
            if role in ["marketbot", "marketing", "summary"]:
                restricted_tools.update(["manage_project"])
            elif role in ["librarian", "rag", "document"]:
                restricted_tools.update(["manage_project", "manage_task"])

        return restricted_tools
