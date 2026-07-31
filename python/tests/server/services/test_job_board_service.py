from unittest.mock import Mock, patch

import pytest

from src.server.services.crawling.clients.job104_client import JobData
from src.server.services.job_board_service import JobBoardService


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
    service = JobBoardService()
    from src.server.services.crawling.clients.job104_client import Job104Crawler
    with patch.object(Job104Crawler, "_fetch_from_104_sync", side_effect=Exception("Network Error")):
        jobs = await service.search_jobs("Data Analyst")

        # In Sync-Thru Real Data Mode, errors return empty list (No mock fallback)
        assert len(jobs) == 0


@pytest.mark.asyncio
async def test_identify_leads_and_save(mock_supabase):
    """
    Test that identify_leads_and_save attempts to insert new leads into Supabase.
    """
    service = JobBoardService()
    # Setup mock jobs
    jobs = [JobData(title="Data Scientist", company="Test Corp", url="http://test/1", identified_need="Need AI")]

    # Setup Supabase Mock chain: table().select().in_().execute() -> data
    mock_select_builder = Mock()
    mock_select_builder.in_.return_value.execute.return_value = Mock(data=[])  # No existing lead

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

    # Execute with mocks to pass the funnel
    with patch.object(service, '_get_hyde_baseline_embedding', return_value=[1.0, 0.0]), \
         patch('src.server.services.embeddings.embedding_service.create_embedding', return_value=[1.0, 0.0]), \
         patch.object(service, '_llm_judge', return_value=True):
        count = await service.identify_leads_and_save(jobs)

    # Assert
    assert count == 1
    mock_supabase.table.assert_called_with("leads")
    mock_table.insert.assert_called_once()

    # Verify insert payload
    inserted_data = mock_table.insert.call_args[0][0]
    assert inserted_data[0]["company_name"] == "Test Corp"
    assert inserted_data[0]["identified_need"] == "Need AI"


@pytest.mark.asyncio
async def test_identify_leads_skips_existing(mock_supabase):
    """
    Test that duplicates are skipped.
    """
    service = JobBoardService()
    jobs = [JobData(title="Data Scientist", company="Test Corp", url="http://test/1")]

    # Mock finding an existing lead
    mock_select_builder = Mock()
    mock_select_builder.in_.return_value.execute.return_value = Mock(data=[{"source_job_url": "http://test/1"}])

    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select_builder

    # Execute
    count = await service.identify_leads_and_save(jobs)

    # Assert
    assert count == 0
    mock_table.insert.assert_not_called()

@pytest.mark.asyncio
async def test_hybrid_funnel_fast_fail_vector():
    """
    Test Assertion 1: When similarity < 0.67, return None immediately.
    _llm_judge and _infer_need should not be called.
    """
    service = JobBoardService()
    job = JobData(title="Plumber", company="Pipes", url="http://p", description="Fix pipes")

    with patch.object(service, '_get_hyde_baseline_embedding', return_value=[1.0, 0.0]), \
         patch('src.server.services.embeddings.embedding_service.create_embedding', return_value=[0.0, 1.0]), \
         patch.object(service, '_llm_judge', return_value=True) as mock_judge, \
         patch.object(service, '_infer_need') as mock_infer:

        # Sim = 0.0 < 0.67
        # We need to invoke the inner _process_single_job.
        # Since it's nested, we test identify_leads_and_save with this job and verify no insert.
        # But wait, identify_leads_and_save suppresses inner exceptions and None returns.

        # Let's mock Supabase for the outer function
        mock_supabase = Mock()
        mock_supabase.table().select().in_().execute().data = []
        service.supabase = mock_supabase

        count = await service.identify_leads_and_save([job])

        assert count == 0
        mock_judge.assert_not_called()
        mock_infer.assert_not_called()

@pytest.mark.asyncio
async def test_hybrid_funnel_fail_llm_judge():
    """
    Test Assertion 2: When similarity >= 0.67 but LLM Judge is NO, return None.
    _infer_need should not be called.
    """
    service = JobBoardService()
    job = JobData(title="AI Engineer", company="Competitor Corp", url="http://c", description="Build AI")

    with patch.object(service, '_get_hyde_baseline_embedding', return_value=[1.0, 0.0]), \
         patch('src.server.services.embeddings.embedding_service.create_embedding', return_value=[1.0, 0.0]), \
         patch.object(service, '_llm_judge', return_value=False) as mock_judge, \
         patch.object(service, '_infer_need') as mock_infer:

        # Sim = 1.0 >= 0.67
        mock_supabase = Mock()
        mock_supabase.table().select().in_().execute().data = []
        service.supabase = mock_supabase

        count = await service.identify_leads_and_save([job])

        assert count == 0
        mock_judge.assert_called_once()
        mock_infer.assert_not_called()

@pytest.mark.asyncio
async def test_hybrid_funnel_pass_both():
    """
    Test Assertion 3: When similarity >= 0.67 and LLM Judge is YES, proceed.
    _infer_need should be called, and lead inserted.
    """
    service = JobBoardService()
    job = JobData(title="System Admin", company="Traditional Corp", url="http://t", description="Need automation")

    with patch.object(service, '_get_hyde_baseline_embedding', return_value=[1.0, 0.0]), \
         patch('src.server.services.embeddings.embedding_service.create_embedding', return_value=[1.0, 0.0]), \
         patch.object(service, '_llm_judge', return_value=True) as mock_judge, \
         patch.object(service, '_infer_need', return_value="Automation need") as mock_infer:

        # Sim = 1.0 >= 0.67, Judge = True
        mock_supabase = Mock()
        mock_supabase.table().select().in_().execute().data = []
        mock_insert = Mock()
        mock_insert.execute().data = [{"id": "new-id", "identified_need": "Automation need"}]
        mock_supabase.table().insert.return_value = mock_insert
        service.supabase = mock_supabase

        count = await service.identify_leads_and_save([job])

        assert count == 1
        mock_judge.assert_called_once()
        mock_infer.assert_called_once()
        mock_supabase.table().insert.assert_called_once()
