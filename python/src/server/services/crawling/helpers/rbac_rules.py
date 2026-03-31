import logging

logger = logging.getLogger(__name__)


async def get_role_based_max_depth(user_role: str | None, credential_service) -> int:
    """
    Fetches max crawl depth from database based on user role.
    Physically isolated for Phase 4.6.16 modularization.

    Args:
        user_role: The role of the user (sales, marketing, manager, admin)
        credential_service: The credential service instance to fetch settings

    Returns:
        int: The maximum crawl depth allowed for the role (default: 1)
    """
    if not user_role:
        return 1

    role_map = {
        "sales": "CRAWL_MAX_DEPTH_SALES",
        "marketing": "CRAWL_MAX_DEPTH_MARKETING",
        "manager": "CRAWL_MAX_DEPTH_MANAGER",
        "admin": "CRAWL_MAX_DEPTH_ADMIN",
        "system_admin": "CRAWL_MAX_DEPTH_ADMIN",
    }

    setting_key = role_map.get(user_role.lower())
    if setting_key:
        try:
            # Use credential_service to fetch from archon_settings
            settings = await credential_service.get_credentials_by_category("crawler_rbac")
            return int(settings.get(setting_key, 1))
        except Exception as e:
            logger.warning(f"Failed to fetch RBAC crawl depth for {user_role}: {e}")
            return 1
    return 1
