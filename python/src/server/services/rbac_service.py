# python/src/server/services/rbac_service.py

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
        content_manager_roles = ["admin", "system_admin", "manager"]
        return current_user_role.lower() in content_manager_roles
