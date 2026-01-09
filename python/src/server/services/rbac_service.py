# python/src/server/services/rbac_service.py

class RBACService:
    """Service for handling Role-Based Access Control (RBAC) logic."""

    def __init__(self):
        # Permission rules: Who can assign to whom.
        self.permissions = {
            # Admin can assign to anyone
            "Admin": ["Admin", "PM", "Engineer", "Marketer", "Market Researcher", "Internal Knowledge Expert", "ai_agent"],
            # PM can assign to Engineers, Marketers, and any AI Agent
            "PM": ["Engineer", "Marketer", "Market Researcher", "Internal Knowledge Expert", "ai_agent"],
            # Engineers can assign to themselves, other Engineers, and any AI Agent
            "Engineer": ["Engineer", "Market Researcher", "Internal Knowledge Expert", "ai_agent"],
            # Marketers can assign to themselves and any AI Agent
            "Marketer": ["Marketer", "Market Researcher", "Internal Knowledge Expert", "ai_agent"]
        }

    def has_permission_to_assign(self, current_user_role: str, assignee_role: str) -> bool:
        """Checks if the current user role has permission to assign tasks to the target role."""
        allowed_roles = self.permissions.get(current_user_role, [])
        return assignee_role in allowed_roles

    def can_manage_content(self, current_user_role: str) -> bool:
        """Checks if the current user role has permission to manage content."""
        if not current_user_role:
            return False
        # Define roles that can manage content (case-insensitive)
        content_manager_roles = ["admin", "system_admin", "manager"]
        return current_user_role.lower() in content_manager_roles
