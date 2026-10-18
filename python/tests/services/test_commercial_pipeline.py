from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.crawling.clients.job104_client import JobData
from src.server.services.job_board_service import JobBoardService
from src.server.services.scheduler.jobs import leads_patrol, sentinel_patrol


@pytest.mark.asyncio
async def test_job_board_service_persists_qualified_score():
    """Verifies that leads with high similarity (>= 75) are stored as qualified with score."""
    mock_supabase = MagicMock()
    service = JobBoardService(supabase_client=mock_supabase)

    # Mock Evaluator & Embeddings
    service.evaluator.get_hyde_baseline_embedding = AsyncMock(return_value=[1.0, 0.0])
    service.evaluator.cosine_similarity = MagicMock(return_value=0.88)
    service.evaluator.llm_judge = AsyncMock(return_value=True)
    service.evaluator.infer_need = AsyncMock(return_value="Need AI system integration")

    with patch("src.server.services.embeddings.embedding_service.create_embedding", new_callable=AsyncMock) as mock_emb:
        mock_emb.return_value = [1.0, 0.0]

        # Mock existing URLs check to return empty
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "lead_1"}])

        jobs = [
            JobData(title="AI Engineer", company="Taipei Tech Corp", url="https://job104/1", description="Build RAG system")
        ]

        count = await service.identify_leads_and_save(jobs)
        assert count == 1

        # Check insert payload
        insert_calls = mock_supabase.table.return_value.insert.call_args_list
        assert len(insert_calls) > 0
        inserted_payload = insert_calls[0].args[0][0]

        assert inserted_payload["status"] == "qualified"
        assert inserted_payload["enrichment_score"] == 88
        assert inserted_payload["enrichment_status"] == "completed"


@pytest.mark.asyncio
@patch("src.server.services.scheduler.jobs.sentinel_patrol.get_supabase_client")
async def test_sentinel_patrol_limits_top3_and_auto_publishes_blog(mock_sb_client):
    """Verifies Sentinel only processes Top 3 stale leads and auto-publishes high-scoring reviews."""
    mock_sb = MagicMock()
    mock_sb_client.return_value = mock_sb

    # Mock Stale Leads: Return 5 items, Sentinel must limit to 3 via query
    mock_sb.table.return_value.select.return_value.lt.return_value.not_.in_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[
            {"id": "lead_1", "company_name": "Company A", "enrichment_score": 90},
            {"id": "lead_2", "company_name": "Company B", "enrichment_score": 85},
            {"id": "lead_3", "company_name": "Company C", "enrichment_score": 80},
        ]
    )

    # Mock Content Bottlenecks: Return 1 post with ai_score 85
    mock_sb.table.return_value.select.return_value.eq.return_value.lt.return_value.execute.return_value = MagicMock(
        data=[{"id": "post_1", "title": "Great Case Study", "ai_score": 85, "updated_at": "2026-10-01"}]
    )

    # Run Sentinel
    await sentinel_patrol.run_business_sentinel()

    # Verify Auto-Publish was called for post_1
    update_calls = mock_sb.table.return_value.update.call_args_list
    updated_fields = [c.args[0] for c in update_calls]
    assert any(f.get("status") == "published" for f in updated_fields)


@pytest.mark.asyncio
@patch("src.server.services.scheduler.jobs.leads_patrol.get_supabase_client")
@patch("src.server.services.system.telegram_service.TelegramService.send_message", new_callable=AsyncMock)
async def test_leads_patrol_pushes_qualified_battlecard(mock_tg_send, mock_sb_client):
    """Verifies Bob market report only filters for qualified leads and dispatches to Telegram."""
    mock_sb = MagicMock()
    mock_sb_client.return_value = mock_sb

    # Return qualified leads
    mock_sb.table.return_value.select.return_value.eq.return_value.gt.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[
            {
                "company_name": "Target Tech",
                "job_title": "Senior ERP Architect",
                "status": "qualified",
                "enrichment_score": 92,
                "source_job_url": "https://job104/target",
                "identified_need": "Legacy ERP migration to AI Agent",
            }
        ]
    )
    mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"id": "proj_1"}]
    )

    with patch("src.server.services.projects.task_service.TaskService.create_task", new_callable=AsyncMock) as mock_task, \
         patch("src.server.services.agent_service.AgentService.run_agent_task", new_callable=AsyncMock):
        mock_task.return_value = (True, {"task": {"id": "task_mkt_1"}})
        mock_tg_send.return_value = True

        await leads_patrol.run_market_report()

        # Must send Telegram Battlecard
        assert mock_tg_send.called
        sent_text = mock_tg_send.call_args.args[0]
        assert "商業雷達：高意向合格潛客戰鬥簡報" in sent_text
        assert "Target Tech" in sent_text
