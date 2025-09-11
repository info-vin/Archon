# python/src/server/services/rbac_service.py

class RBACService:
    """Service for handling Role-Based Access Control (RBAC) logic."""

    def __init__(self):
        # Permission rules: Who can assign to whom.
        self.permissions = {
            # Admin can assign to anyone
            "Admin": ["Admin", "PM", "Engineer", "Marketer", "Market Researcher", "Internal Knowledge Expert"],
            # PM can assign to Engineers, Marketers, and any AI Agent
            "PM": ["Engineer", "Marketer", "Market Researcher", "Internal Knowledge Expert"],
            # Engineers can assign to themselves, other Engineers, and any AI Agent
            "Engineer": ["Engineer", "Market Researcher", "Internal Knowledge Expert"],
            # Marketers can assign to themselves and any AI Agent
            "Marketer": ["Marketer", "Market Researcher", "Internal Knowledge Expert"]
        }

    def has_permission_to_assign(self, current_user_role: str, assignee_role: str) -> bool:
        """Checks if the current user role has permission to assign tasks to the target role."""
        allowed_roles = self.permissions.get(current_user_role, [])
        return assignee_role in allowed_roles
