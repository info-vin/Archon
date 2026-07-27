from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.services.enrichment_service import EnrichmentService


@pytest.mark.asyncio
async def test_enrich_lead_success():
    """
    Test that enrich_lead updates status to success.
    """
    mock_supabase = MagicMock()
    # Mock finding the lead (now expects a list because single() was removed)
    mock_supabase.table().select().eq().execute.return_value.data = [{
        "id": "lead-123",
        "company_name": "Test Corp",
        "enrichment_status": None,
    }]

    with (
        patch("server.services.enrichment_service.get_supabase_client", return_value=mock_supabase),
        patch(
            "server.services.credential_service.credential_service.get_credential", new_callable=AsyncMock
        ) as mock_get_cred,
        patch("asyncio.sleep", return_value=None),
    ):  # Skip sleep
        # Mock ENABLE_REAL_ENRICHMENT = False (default)
        mock_get_cred.return_value = "false"

        success = await EnrichmentService.enrich_lead("lead-123")

        assert success is True
        # Verify update call
        mock_supabase.table().update.assert_called()
        args, _ = mock_supabase.table().update.call_args
        assert args[0]["enrichment_status"] == "success"
        # Score calculation: 20 (base) + 20 (mock_email) + 30 (funding in news) = 70
        assert args[0]["enrichment_score"] == 70


@pytest.mark.asyncio
async def test_prune_stale_leads():
    """
    Test that prune_stale_leads archives old leads using batch update.
    """
    mock_supabase = MagicMock()

    # Mock the update chain and final response
    # In batch mode, we call .update().lt().lt().neq().neq().execute()
    mock_update_chain = mock_supabase.table().update.return_value
    mock_update_chain.lt.return_value = mock_update_chain
    mock_update_chain.neq.return_value = mock_update_chain

    # The final .execute() returns the list of modified records
    mock_update_chain.execute.return_value.data = [
        {"id": "lead-old-1", "status": "archived"},
        {"id": "lead-old-2", "status": "archived"},
    ]

    with patch("server.services.enrichment_service.get_supabase_client", return_value=mock_supabase):
        count = await EnrichmentService.prune_stale_leads()

        # Should return 2 based on the mock data length
        assert count == 2

        # Verify single batch update call instead of individual ones
        mock_supabase.table().update.assert_called_once()

        # Verify parameters of the update
        args, _ = mock_supabase.table().update.call_args
        assert args[0]["status"] == "archived"
        assert args[0]["auto_archived_reason"] == "stale_low_quality"
