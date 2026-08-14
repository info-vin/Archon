import os
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


@pytest.fixture(autouse=True)
def setup_agents_md(tmp_path, monkeypatch):
    """
    Mock the Path resolution so that it finds a fake AGENTS.md.
    """
    fake_project_root = tmp_path
    agents_md = fake_project_root / "AGENTS.md"
    agents_md.write_text("Test Core Text", encoding="utf-8")

    original_exists = os.path.exists
    original_open = open

    def mocked_exists(path):
        if "AGENTS.md" in str(path):
            return True
        return original_exists(path)

    def mocked_open(path, *args, **kwargs):
        if "AGENTS.md" in str(path):
            return original_open(str(agents_md), *args, **kwargs)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("os.path.exists", mocked_exists)
    monkeypatch.setattr("builtins.open", mocked_open)


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
    jobs = [JobData(title="Data Scientist", company="Test Corp", url="http://test/1", identified_need="Need AI")]

    mock_select_builder = Mock()
    mock_select_builder.in_.return_value.execute.return_value = Mock(data=[])  # No existing lead

    mock_insert_builder = Mock()
    mock_insert_builder.execute.return_value = Mock(data=[{"id": "new-id"}])

    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select_builder
    mock_table.insert.return_value = mock_insert_builder

    # BOUNDARY MOCKS: Mock LLM response and Embeddings instead of internal logic!
    async def mock_generate_llm_response(prompt_name, **kwargs):
        if prompt_name == "ALICE_HYDE_BASELINE":
            return "HyDE Baseline Content"
        elif prompt_name == "ALICE_LEAD_JUDGE":
            return "YES"
        elif prompt_name == "ALICE_INFER_NEED":
            return "Need AI"
        return ""

    with patch.object(service.evaluator, 'generate_llm_response', side_effect=mock_generate_llm_response), \
         patch('src.server.services.embeddings.embedding_service.create_embedding', return_value=[1.0, 0.0]):

        # Make the similarity calculation return 1.0 (pass the threshold 0.67)
        with patch.object(service.evaluator, 'cosine_similarity', return_value=1.0):
            count = await service.identify_leads_and_save(jobs)

    assert count == 1
    mock_supabase.table.assert_called_with("leads")
    mock_table.insert.assert_called_once()
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

    mock_select_builder = Mock()
    mock_select_builder.in_.return_value.execute.return_value = Mock(data=[{"source_job_url": "http://test/1"}])

    mock_table = Mock()
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select_builder

    count = await service.identify_leads_and_save(jobs)

    assert count == 0
    mock_table.insert.assert_not_called()


@pytest.mark.asyncio
async def test_hybrid_funnel_fast_fail_vector():
    """
    Test Assertion 1: When similarity < 0.67, return None immediately.
    _llm_judge and _infer_need should not be called because LLM is bypassed.
    """
    service = JobBoardService()
    job = JobData(title="Plumber", company="Pipes", url="http://p", description="Fix pipes")

    mock_supabase = Mock()
    mock_supabase.table().select().in_().execute().data = []
    service.supabase = mock_supabase

    async def mock_generate_llm_response(prompt_name, **kwargs):
        if prompt_name == "ALICE_HYDE_BASELINE":
            return "HyDE Baseline Content"
        return "FAIL" # Should not be called for others

    with patch.object(service.evaluator, 'generate_llm_response', side_effect=mock_generate_llm_response) as mock_llm, \
         patch('src.server.services.embeddings.embedding_service.create_embedding', return_value=[0.0, 1.0]):

        # Sim = 0.0 < 0.67
        with patch.object(service.evaluator, 'cosine_similarity', return_value=0.0):
            count = await service.identify_leads_and_save([job])

    assert count == 0
    # LLM should only be called for ALICE_HYDE_BASELINE, not for JUDGE or INFER_NEED
    calls = mock_llm.call_args_list
    assert len(calls) == 1
    assert calls[0][1]["prompt_name"] == "ALICE_HYDE_BASELINE"


@pytest.mark.asyncio
async def test_hybrid_funnel_fail_llm_judge():
    """
    Test Assertion 2: When similarity >= 0.67 but LLM Judge is NO, return None.
    """
    service = JobBoardService()
    job = JobData(title="AI Engineer", company="Competitor Corp", url="http://c", description="Build AI")

    mock_supabase = Mock()
    mock_supabase.table().select().in_().execute().data = []
    service.supabase = mock_supabase

    async def mock_generate_llm_response(prompt_name, **kwargs):
        if prompt_name == "ALICE_HYDE_BASELINE":
            return "HyDE Baseline Content"
        elif prompt_name == "ALICE_LEAD_JUDGE":
            return "NO" # Fail the judge
        return "FAIL"

    with patch.object(service.evaluator, 'generate_llm_response', side_effect=mock_generate_llm_response) as mock_llm, \
         patch('src.server.services.embeddings.embedding_service.create_embedding', return_value=[1.0, 0.0]):

        # Sim = 1.0 >= 0.67
        with patch.object(service.evaluator, 'cosine_similarity', return_value=1.0):
            count = await service.identify_leads_and_save([job])

    assert count == 0
    # Should be called for BASELINE and JUDGE, but not INFER_NEED
    calls = mock_llm.call_args_list
    assert len(calls) == 2
    prompt_names = [call[1]["prompt_name"] for call in calls]
    assert "ALICE_HYDE_BASELINE" in prompt_names
    assert "ALICE_LEAD_JUDGE" in prompt_names
    assert "ALICE_INFER_NEED" not in prompt_names


@pytest.mark.asyncio
async def test_hybrid_funnel_missing_agents_md(monkeypatch):
    """
    Test Fault Tolerance: If AGENTS.md is missing, _get_core_text returns None,
    and the funnel fails fast without crashing.
    """
    service = JobBoardService()
    job = JobData(title="System Admin", company="Traditional Corp", url="http://t", description="Need automation")

    # Undo the fixture's patch to simulate missing file
    original_exists = os.path.exists
    def mocked_exists(path):
        if "AGENTS.md" in str(path):
            return False # Force it to fail!
        return original_exists(path)
    monkeypatch.setattr("os.path.exists", mocked_exists)

    mock_supabase = Mock()
    mock_supabase.table().select().in_().execute().data = []
    service.supabase = mock_supabase

    with patch.object(service.evaluator, 'generate_llm_response') as mock_llm, \
         patch('src.server.services.embeddings.embedding_service.create_embedding') as mock_embed:

        count = await service.identify_leads_and_save([job])

    # Should fail safely
    assert count == 0
    # Embeddings shouldn't even be called because core_text is missing
    mock_embed.assert_not_called()
    mock_llm.assert_not_called()

@pytest.mark.asyncio
async def test_auto_fetch_pagination_fallback():
    """
    Test that auto_fetch_daily_leads iterates through pages for a keyword if no leads are found,
    but stops paging for that keyword once keyword_new_leads > 0.
    """
    service = JobBoardService()

    # Mock settings
    mock_config = Mock()
    mock_config.crawler_job_keywords = "Python,AI"
    mock_config.crawler_job_limit = 2
    mock_config.crawler_max_pages = 2
    mock_config.crawler_waf_delay_min = 0.0
    mock_config.crawler_waf_delay_max = 0.0

    with patch.object(service, '_get_crawler_config', return_value=mock_config):

        async def mock_search_jobs(keyword, limit, client, page):
            return [JobData(title=f"{keyword} Job P{page}", company="Test", url="http://test", description="")]

        with patch.object(service, 'search_jobs', side_effect=mock_search_jobs) as mock_search:

            async def mock_identify_leads(jobs):
                # Python finds a lead on page 1
                if "Python" in jobs[0].title and "P1" in jobs[0].title:
                    return 1
                # AI finds a lead on page 2
                if "AI" in jobs[0].title and "P2" in jobs[0].title:
                    return 1
                return 0

            with patch.object(service, 'identify_leads_and_save', side_effect=mock_identify_leads):
                service.crawler = Mock()
                service.crawler.create_session.return_value = Mock()

                total = await service.auto_fetch_daily_leads()

                # Should return 2 leads (1 from Python P1, 1 from AI P2)
                assert total == 2

                # search_jobs should have been called 3 times:
                # Python P1 (success -> breaks)
                # AI P1 (fail -> continues)
                # AI P2 (success -> breaks)
                assert mock_search.call_count == 3

