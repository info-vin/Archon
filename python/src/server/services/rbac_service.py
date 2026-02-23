# python/src/server/services/rbac_service.py

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client

logger = get_logger(__name__)

class RBACService:
    """Service for handling Role-Based Access Control (RBAC) logic."""

    def __init__(self):
        # Permission rules: Who can assign to whom.
        # Roles match permissions.py (lowercase) + 'ai_agent'
        # NOTE: 'member' is mapped to 'employee' logic for simplicity if not explicitly defined
        self.permissions = {
            # Admin can assign to anyone
            "admin": ["admin", "system_admin", "manager", "employee", "member", "marketing", "sales", "ai_agent"],
            "system_admin": ["admin", "system_admin", "manager", "employee", "member", "marketing", "sales", "ai_agent"],

            # Manager can assign to their team (generic simplification) and agents
            "manager": ["manager", "employee", "member", "marketing", "sales", "ai_agent"],

            # Employees/Members can assign to themselves and generic agents
            "employee": ["employee", "member", "ai_agent"],
            "member": ["employee", "member", "ai_agent"],

            # Marketers can assign to themselves and Marketing Agents
            "marketing": ["marketing", "ai_agent"],

            # Sales can assign to themselves and Sales Agents
            "sales": ["sales", "ai_agent"],

            # Legacy/Alias support
            "pm": ["manager", "employee", "member", "marketing", "sales", "ai_agent"],
            "engineer": ["employee", "member", "ai_agent"],
        }

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
            "sales": "SALES"
        }
        suffix = role_map.get(role, "SALES") # Default to strictest (SALES) for unknown roles

        # Default safe values if DB fetch fails
        constraints = {
            "max_depth": 2,
            "max_concurrent": 3,
            "allowed_domains": ["104.com.tw", "github.com", "google.com"]
        }

        try:
            supabase = get_supabase_client()
            # 1. Fetch static settings from archon_settings
            keys = [f"CRAWL_MAX_DEPTH_{suffix}", f"CRAWL_CONCURRENT_MAX_{suffix}", "CRAWL_ALLOWED_DOMAINS_RESTRICTED"]
            result = supabase.table("archon_settings").select("key, value").in_("key", keys).execute()

            if result.data:
                settings = {item['key']: item['value'] for item in result.data}

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
            dynamic_result = supabase.table("archon_crawler_targets")\
                .select("whitelist, target_url")\
                .eq("is_active", True)\
                .execute()

            if dynamic_result.data:
                from typing import cast
                allowed_domains = cast(list[str], constraints["allowed_domains"])

                for target in dynamic_result.data:
                    # 加入主網址網域 (Domain) 作為基本許可
                    from urllib.parse import urlparse
                    domain = urlparse(target['target_url']).netloc
                    if domain and domain not in allowed_domains:
                        allowed_domains.append(domain)

                    # 加入 David 設定的詳細白名單 Patterns
                    if target.get('whitelist'):
                        for pattern in target['whitelist']:
                            if pattern and pattern not in allowed_domains:
                                allowed_domains.append(pattern)
        except Exception as e:
            logger.error(f"Failed to fetch crawler constraints for role {role}: {e}")

        return constraints

    def has_permission_to_assign(self, current_user_role: str, assignee_role: str) -> bool:
        """Checks if the current user role has permission to assign tasks to the target role."""
        if not current_user_role or not assignee_role:
            return False

        current_role = current_user_role.lower()
        target_role = assignee_role.lower()

        allowed_roles = self.permissions.get(current_role, [])

        # 1. Direct role match
        if target_role in allowed_roles:
            return True

        # 2. Agent wildcard check
        # If the target is an 'ai_agent' role, it should be allowed if 'ai_agent' is in the list.
        if target_role == "ai_agent" and "ai_agent" in allowed_roles:
            return True

        return False

    def get_assignable_roles(self, current_user_role: str) -> list[str]:
        """Returns a list of roles that the current user can assign tasks to."""
        if not current_user_role:
            return []
        return self.permissions.get(current_user_role.lower(), [])

    def can_manage_content(self, current_user_role: str) -> bool:
        """Checks if the current user role has permission to manage content."""
        if not current_user_role:
            return False
        # Define roles that can manage content (case-insensitive)
        # Updated Phase 4.4: Sales and Marketing are content creators too.
        content_manager_roles = ["admin", "system_admin", "manager", "marketing", "sales"]
        return current_user_role.lower() in content_manager_roles
