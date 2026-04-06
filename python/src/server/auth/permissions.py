# python/src/server/auth/permissions.py


# --- Permission Scopes ---

# Task Management
TASK_CREATE = "task:create"
TASK_READ_OWN = "task:read:own"
TASK_READ_TEAM = "task:read:team"
TASK_READ_ALL = "task:read:all"
TASK_UPDATE_OWN = "task:update:own"
TASK_UPDATE_ALL = "task:update:all"  # Admin override

# Agent Collaboration
AGENT_TRIGGER_DEV = "agent:trigger:dev"  # DevBot
AGENT_TRIGGER_MKT = "agent:trigger:mkt"  # MarketBot
AGENT_TRIGGER_KNOW = "agent:trigger:know"  # Knowledge Agent

# Code/Content Approval
CODE_APPROVE = "code:approve"
CONTENT_PUBLISH = "content:publish"

# Business Intelligence
STATS_VIEW_OWN = "stats:view:own"
STATS_VIEW_TEAM = "stats:view:team"
STATS_VIEW_ALL = "stats:view:all"
LEADS_VIEW_ALL = "leads:view:all"

# Content Loop (Phase 4.6)
CONTENT_REJECT = "content:reject"
INFO_REQUEST = "info:request"

# System Management
USER_MANAGE = "user:manage"  # Create user, change role
USER_MANAGE_TEAM = "user:manage:team"  # Manage users in same department
MCP_MANAGE = "mcp:manage"  # Configure tools
BRAND_ASSET_MANAGE = "brand:manage"  # Manage logos, colors, assets

# --- Role Definition ---

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "system_admin": {
        TASK_CREATE,
        TASK_READ_OWN,
        TASK_READ_TEAM,
        TASK_READ_ALL,
        TASK_UPDATE_OWN,
        TASK_UPDATE_ALL,
        AGENT_TRIGGER_DEV,
        AGENT_TRIGGER_MKT,
        AGENT_TRIGGER_KNOW,
        CODE_APPROVE,
        CONTENT_PUBLISH,
        CONTENT_REJECT,
        INFO_REQUEST,
        STATS_VIEW_OWN,
        STATS_VIEW_TEAM,
        STATS_VIEW_ALL,
        LEADS_VIEW_ALL,
        USER_MANAGE,
        MCP_MANAGE,
        BRAND_ASSET_MANAGE,
        USER_MANAGE_TEAM,
    },
    "admin": {  # Alias for system_admin for backward compatibility
        TASK_CREATE,
        TASK_READ_OWN,
        TASK_READ_TEAM,
        TASK_READ_ALL,
        TASK_UPDATE_OWN,
        TASK_UPDATE_ALL,
        AGENT_TRIGGER_DEV,
        AGENT_TRIGGER_MKT,
        AGENT_TRIGGER_KNOW,
        CODE_APPROVE,
        CONTENT_PUBLISH,
        CONTENT_REJECT,
        INFO_REQUEST,
        STATS_VIEW_OWN,
        STATS_VIEW_TEAM,
        STATS_VIEW_ALL,
        LEADS_VIEW_ALL,
        USER_MANAGE,
        MCP_MANAGE,
        BRAND_ASSET_MANAGE,
        USER_MANAGE_TEAM,
    },
    "manager": {
        TASK_CREATE,
        TASK_READ_TEAM,
        TASK_UPDATE_OWN,
        AGENT_TRIGGER_DEV,
        AGENT_TRIGGER_MKT,
        AGENT_TRIGGER_KNOW,
        CODE_APPROVE,
        CONTENT_PUBLISH,
        CONTENT_REJECT,
        INFO_REQUEST,
        STATS_VIEW_TEAM,
        LEADS_VIEW_ALL,
        USER_MANAGE_TEAM,
        MCP_MANAGE,
        BRAND_ASSET_MANAGE,
    },
    "employee": {  # Generic Employee
        TASK_CREATE,
        TASK_READ_OWN,
        TASK_UPDATE_OWN,
        AGENT_TRIGGER_KNOW,
        STATS_VIEW_OWN,
    },
    "sales": {TASK_CREATE, TASK_READ_OWN, TASK_READ_TEAM, TASK_UPDATE_OWN, AGENT_TRIGGER_MKT, LEADS_VIEW_ALL},
    "marketing": {  # Bob
        TASK_CREATE,
        TASK_READ_OWN,
        TASK_READ_TEAM,
        TASK_UPDATE_OWN,
        AGENT_TRIGGER_MKT,
        AGENT_TRIGGER_KNOW,
        STATS_VIEW_OWN,
        LEADS_VIEW_ALL,
        BRAND_ASSET_MANAGE,
        INFO_REQUEST,
    },
}

# --- All Permissions List (for UI Matrix) ---
ALL_PERMISSIONS = [
    TASK_CREATE,
    TASK_READ_TEAM,
    TASK_READ_ALL,
    TASK_UPDATE_ALL,
    AGENT_TRIGGER_DEV,
    AGENT_TRIGGER_MKT,
    AGENT_TRIGGER_KNOW,
    CODE_APPROVE,
    CONTENT_PUBLISH,
    CONTENT_REJECT,
    INFO_REQUEST,
    STATS_VIEW_TEAM,
    STATS_VIEW_ALL,
    LEADS_VIEW_ALL,
    USER_MANAGE,
    USER_MANAGE_TEAM,
    MCP_MANAGE,
    BRAND_ASSET_MANAGE,
]


def get_role_permissions(role: str) -> set[str]:
    """Returns the set of permissions for a given role (case-insensitive)."""
    return ROLE_PERMISSIONS.get(role.lower(), set())


def has_permission(user: dict, permission: str) -> bool:
    """
    Checks if a user has a specific permission.
    Args:
        user: User dictionary (usually from profiles table)
        permission: The permission scope to check (e.g. TASK_CREATE)
    """
    if not user:
        return False

    # 1. Check per-user overrides first (High priority)
    overrides = user.get("permission_overrides") or {}
    if permission in overrides:
        return bool(overrides[permission])

    # 2. Fallback to role-based permissions
    user_role = user.get("role", "viewer").lower()
    role_perms = get_role_permissions(user_role)
    return permission in role_perms
