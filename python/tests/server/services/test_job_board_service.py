from unittest.mock import Mock, patch

import pytest

from src.server.services.job_board_service import JobBoardService, JobData


@pytest.fixture
def mock_supabase():
    with patch("src.server.services.job_board_service.get_supabase_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        yield mock_client

@pytest.mark.asyncio
async def test_search_jobs_fallback_to_mock():
    """
    Test that search_jobs falls back to mock data when API fails or returns empty,
    and correctly infers needs.
    """
    # Mock _fetch_from_104 to raise an exception
    with patch.object(JobBoardService, "_fetch_from_104", side_effect=Exception("Network Error")):
        jobs = await JobBoardService.search_jobs("Data Analyst")

        assert len(jobs) > 0
        assert jobs[0].company == "Retail Corp"  # Should use updated mock data
        assert jobs[0].source == "mock"
        assert "BI Tool" in jobs[0].identified_need  # Need should be inferred

@pytest.mark.asyncio
async def test_identify_leads_and_save(mock_supabase):
    """
    Test that identify_leads_and_save attempts to insert new leads into Supabase.
    """
    # Setup mock jobs
    jobs = [
        JobData(
            title="Data Scientist",
            company="Test Corp",
            url="http://test/1",
            identified_need="Need AI"
        )
    ]

    # Setup Supabase Mock chain: table().select().eq().eq().execute() -> data
    mock_select_builder = Mock()
    mock_select_builder.eq.return_value.eq.return_value.execute.return_value = Mock(data=[]) # No existing lead

    mock_insert_builder = Mock()
    mock_insert_builder.execute.return_value = Mock(data=[{"id": "new-id"}])

    # Configure table() to return different builders based on table name (optional but good practice)
    # Simplified: Just make table() return a builder that can handle both flows
    mock_table = Mock()
    mock_supabase.table.return_value = mock_table

    # Chain for SELECT
    mock_table.select.return_value = mock_select_builder

    # Chain for INSERT
    mock_table.insert.return_value = mock_insert_builder

    # Execute
    count = await JobBoardService.identify_leads_and_save(jobs)

    # Assert
    assert count == 1
    mock_supabase.table.assert_called_with("leads")
    mock_table.insert.assert_called_once()

    # Verify insert payload
    inserted_data = mock_table.insert.call_args[0][0]
    assert inserted_data["company_name"] == "Test Corp"
    assert inserted_data["identified_need"] == "Need AI"

@pytest.mark.asyncio
async def test_identify_leads_skips_existing(mock_supabase):
    """
    Test that duplicates are skipped.
    """
    jobs = [JobData(title="Data Scientist", company="Test Corp", url="http://test/1")]

    # Mock finding an existing lead
    mock_select_builder = Mock()
    mock_select_builder.eq.return_value.eq.return_value.execute.return_value = Mock(data=[{"id": "existing-id"}])

    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select_builder

    # Execute
    count = await JobBoardService.identify_leads_and_save(jobs)

    # Assert
    assert count == 0
    mock_table.insert.assert_not_called()
