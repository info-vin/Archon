from unittest.mock import patch

import pytest

from src.server.api_routes.marketing_api import get_marketing_stats, run_sentinel_manual
from src.server.models.auth_models import UserProfileDTO
from src.server.schemas.marketing import MarketingStatsResponse, SentinelRunResponse


@pytest.mark.asyncio
async def test_get_marketing_stats_success():
    """Verify get_marketing_stats returns a valid MarketingStatsResponse model."""
    user = UserProfileDTO(id="test-user-id", role="marketing", email="marketing@example.com")

    mock_stats_dict = {
        "total_leads": 42,
        "total_blog_posts": 10,
        "conversion_rate": 23.81,
        "active_campaigns": 10,
        "last_updated": "2026-03-20T10:00:00Z",
    }

    with patch("src.server.services.marketing_service.MarketingService.get_marketing_stats") as mock_method:
        mock_method.return_value = mock_stats_dict

        res = await get_marketing_stats(current_user=user)

        assert isinstance(res, MarketingStatsResponse)
        assert res.total_leads == 42
        assert res.total_blog_posts == 10
        assert res.conversion_rate == 23.81
        assert res.active_campaigns == 10
        assert res.last_updated == "2026-03-20T10:00:00Z"


@pytest.mark.asyncio
async def test_run_sentinel_manual_success():
    """Verify run_sentinel_manual returns a valid SentinelRunResponse model."""
    user_dict = {"id": "test-admin-id", "role": "admin", "permissions": ["agent:trigger_mkt"]}

    mock_sentinel_dict = {
        "status": "triggered",
        "message": "Sentinel scan started in background.",
    }

    with patch("src.server.services.marketing_service.MarketingService.run_sentinel") as mock_method:
        mock_method.return_value = mock_sentinel_dict

        res = await run_sentinel_manual(current_user=user_dict)

        assert isinstance(res, SentinelRunResponse)
        assert res.status == "triggered"
        assert res.message == "Sentinel scan started in background."
