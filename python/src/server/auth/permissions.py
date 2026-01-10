# python/src/server/auth/permissions.py


# --- Permission Scopes ---

# Task Management
TASK_CREATE = "task:create"
TASK_READ_OWN = "task:read:own"
TASK_READ_TEAM = "task:read:team"
TASK_READ_ALL = "task:read:all"
TASK_UPDATE_OWN = "task:update:own"
TASK_UPDATE_ALL = "task:update:all" # Admin override

# Agent Collaboration
AGENT_TRIGGER_DEV = "agent:trigger:dev"     # DevBot
AGENT_TRIGGER_MKT = "agent:trigger:mkt"     # MarketBot
AGENT_TRIGGER_KNOW = "agent:trigger:know"   # Knowledge Agent

# Code/Content Approval
CODE_APPROVE = "code:approve"
CONTENT_PUBLISH = "content:publish"

# Business Intelligence
STATS_VIEW_OWN = "stats:view:own"
STATS_VIEW_TEAM = "stats:view:team"
STATS_VIEW_ALL = "stats:view:all"
LEADS_VIEW_ALL = "leads:view:all"

# System Management
USER_MANAGE = "user:manage" # Create user, change role
MCP_MANAGE = "mcp:manage"   # Configure tools

# --- Role Definition ---

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "system_admin": {
        TASK_CREATE, TASK_READ_ALL, TASK_UPDATE_ALL,
        AGENT_TRIGGER_DEV, AGENT_TRIGGER_MKT, AGENT_TRIGGER_KNOW,
        CODE_APPROVE, CONTENT_PUBLISH,
        STATS_VIEW_ALL, LEADS_VIEW_ALL,
        USER_MANAGE, MCP_MANAGE
    },
    "admin": {  # Alias for system_admin for backward compatibility
        TASK_CREATE, TASK_READ_ALL, TASK_UPDATE_ALL,
        AGENT_TRIGGER_DEV, AGENT_TRIGGER_MKT, AGENT_TRIGGER_KNOW,
        CODE_APPROVE, CONTENT_PUBLISH,
        STATS_VIEW_ALL, LEADS_VIEW_ALL,
        USER_MANAGE, MCP_MANAGE
    },
    "manager": { # Charlie
        TASK_CREATE, TASK_READ_TEAM, TASK_UPDATE_OWN,
        AGENT_TRIGGER_DEV, AGENT_TRIGGER_MKT, AGENT_TRIGGER_KNOW,
        CODE_APPROVE, CONTENT_PUBLISH,
        STATS_VIEW_TEAM, LEADS_VIEW_ALL
    },
    "employee": { # Generic Employee
        TASK_CREATE, TASK_READ_OWN, TASK_UPDATE_OWN,
        AGENT_TRIGGER_KNOW,
        STATS_VIEW_OWN
    },
    "sales": { # Alice
        TASK_CREATE, TASK_READ_OWN, TASK_UPDATE_OWN,
        AGENT_TRIGGER_MKT,
        STATS_VIEW_OWN, LEADS_VIEW_ALL
    },
    "marketing": { # Bob
        TASK_CREATE, TASK_READ_OWN, TASK_UPDATE_OWN,
        AGENT_TRIGGER_MKT, AGENT_TRIGGER_KNOW,
        STATS_VIEW_OWN, LEADS_VIEW_ALL
    }
}

def get_role_permissions(role: str) -> set[str]:
    """Returns the set of permissions for a given role (case-insensitive)."""
    return ROLE_PERMISSIONS.get(role.lower(), set())
