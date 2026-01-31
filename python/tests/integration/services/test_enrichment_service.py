from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.services.enrichment_service import EnrichmentService


@pytest.mark.asyncio
async def test_enrich_lead_success():
    """
    Test that enrich_lead updates status to success.
    """
    mock_supabase = MagicMock()
    # Mock finding the lead
    mock_supabase.table().select().eq().single().execute.return_value.data = {
        "id": "lead-123",
        "company_name": "Test Corp",
        "enrichment_status": None
    }

    with patch("server.services.enrichment_service.get_supabase_client", return_value=mock_supabase), \
         patch("server.services.credential_service.credential_service.get_credential", new_callable=AsyncMock) as mock_get_cred, \
         patch("asyncio.sleep", return_value=None): # Skip sleep

        # Mock ENABLE_REAL_ENRICHMENT = False (default)
        mock_get_cred.return_value = "false"

        success = await EnrichmentService.enrich_lead("lead-123")

        assert success is True
        # Verify update call
        mock_supabase.table().update.assert_called()
        args, _ = mock_supabase.table().update.call_args
        assert args[0]["enrichment_status"] == "success"
        assert args[0]["enrichment_score"] == 85

@pytest.mark.asyncio
async def test_prune_stale_leads():
    """
    Test that prune_stale_leads archives old leads.
    """
    mock_supabase = MagicMock()
    # Mock finding stale leads
    mock_supabase.table().select().lt().neq().neq().execute.return_value.data = [
        {"id": "lead-old-1", "enrichment_status": "failed", "enrichment_score": 0},
        {"id": "lead-old-2", "enrichment_status": "pending", "enrichment_score": 20}
    ]

    with patch("server.services.enrichment_service.get_supabase_client", return_value=mock_supabase):
        count = await EnrichmentService.prune_stale_leads()

        assert count == 2
        # Verify update call (called twice)
        assert mock_supabase.table().update.call_count == 2
        # Check argument of last call
        args, _ = mock_supabase.table().update.call_args
        assert args[0]["status"] == "archived"
        assert args[0]["auto_archived_reason"] == "stale_low_quality"
