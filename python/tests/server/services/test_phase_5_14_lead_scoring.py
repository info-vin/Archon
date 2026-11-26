from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.crawling.clients.job104_client import JobData
from src.server.services.crawling.lead_evaluator import LeadJudgeResult, parse_judge_response
from src.server.services.job_board_service import JobBoardService
from src.server.services.scheduler.jobs import leads_patrol


class TestStructuredJudgeParsing:
    def test_parses_valid_json_and_fenced_json(self):
        res = parse_judge_response('{"category": "A", "confidence": 0.87, "reason": "製造業導入自動化"}')
        assert res.category == "A"
        assert res.confidence == 0.87
        assert res.is_qualified is True

        fenced = parse_judge_response('```json\n{"category": "C", "confidence": 0.95, "reason": "SI 同業"}\n```')
        assert fenced.category == "C"
        assert fenced.is_qualified is False
        assert "SI" in fenced.reason

    def test_fails_safe_to_x_on_invalid_output(self):
        bad = parse_judge_response("YES definitely a lead")
        assert bad.category == "X"
        assert bad.confidence == 0.0
        assert bad.is_qualified is False
        assert "Unparseable" in bad.reason


class TestPhase514QuotaAndG1G3G4:
    @pytest.mark.asyncio
    async def test_g1_bulk_logs_rejected_leads_and_applies_ab_60_40_quota(self):
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "x"}])

        service = JobBoardService(supabase_client=mock_supabase)
        service.evaluator.get_hyde_baseline_embedding = AsyncMock(return_value=[1.0, 0.0])
        service.evaluator.cosine_similarity = MagicMock(return_value=0.85)
        service.evaluator.infer_need = AsyncMock(return_value="自動化需求")

        # 3 A leads + 4 B leads + 1 C rejected lead
        jobs = [
            JobData(title=f"A Job {i}", company=f"A Corp {i}", url=f"https://104/a{i}") for i in range(3)
        ] + [
            JobData(title=f"B Job {i}", company=f"B Corp {i}", url=f"https://104/b{i}") for i in range(4)
        ] + [
            JobData(title="SI Eng", company="SI Competitor", url="https://104/c1")
        ]

        async def _fake_judge(job: JobData) -> LeadJudgeResult:
            if job.company.startswith("A Corp"):
                return LeadJudgeResult(category="A", confidence=0.90, reason="A 類製造業")
            if job.company.startswith("B Corp"):
                idx = int(job.company.split()[-1])
                return LeadJudgeResult(category="B", confidence=0.80 + idx * 0.02, reason="B 類小型潛客")
            return LeadJudgeResult(category="C", confidence=0.95, reason="排除 SI 系統整合商")

        service.evaluator.evaluate_lead_structured = AsyncMock(side_effect=_fake_judge)

        with patch("src.server.services.embeddings.embedding_service.create_embedding", new_callable=AsyncMock, return_value=[1.0, 0.0]):
            await service.identify_leads_and_save(jobs)

        # Inspect table calls: should have archon_logs bulk insert (G1) and leads insert (quota applied)
        table_calls = [c.args[0] for c in mock_supabase.table.call_args_list]
        assert "archon_logs" in table_calls
        assert "leads" in table_calls

        insert_payloads = [c.args[0] for c in mock_supabase.table.return_value.insert.call_args_list]
        # G1 log payload
        g1_payload = next(p for p in insert_payloads if isinstance(p, list) and p and p[0].get("source") == "job_board_service_triage")
        assert len(g1_payload) == 1
        assert g1_payload[0]["details"]["category"] == "C"
        assert "SI" in g1_payload[0]["details"]["reason"]

        # Leads payload: 3 A qualified + floor(3 * 40 / 60) = 2 B qualified; remaining 2 B demoted to archived
        leads_payload = next(p for p in insert_payloads if isinstance(p, list) and p and "company_name" in p[0])
        assert all(row["status"] in ("qualified", "archived") for row in leads_payload)  # Never 'discarded'
        qual_a = [r for r in leads_payload if r["status"] == "qualified" and "[A類" in r["identified_need"]]
        qual_b = [r for r in leads_payload if r["status"] == "qualified" and "[B類" in r["identified_need"]]
        arch_b = [r for r in leads_payload if r["status"] == "archived" and "[B類" in r["identified_need"]]
        assert len(qual_a) == 3
        assert len(qual_b) == 2
        assert len(arch_b) == 2

    @pytest.mark.asyncio
    async def test_g3_leads_patrol_logs_start_and_error(self):
        logged_events: list[tuple[str, str, str]] = []

        def _capture(job_name: str, phase: str, message: str, details=None, level: str = "INFO") -> None:
            logged_events.append((job_name, phase, level))

        with (
            patch.object(leads_patrol, "log_patrol_event", side_effect=_capture),
            patch("src.server.services.job_board_service.JobBoardService", side_effect=RuntimeError("104 WAF down")),
        ):
            await leads_patrol.run_auto_fetch_leads()

        assert ("alice_auto_fetch", "start", "INFO") in logged_events
        assert ("alice_auto_fetch", "error", "ERROR") in logged_events

    @pytest.mark.parametrize("status_code", [403, 429, 503])
    def test_job104_search_api_raises_blocked_on_403_429_and_503(self, status_code: int):
        from src.server.services.crawling.clients.job104_client import CrawlerBlockedException, Job104Crawler

        crawler = Job104Crawler()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_client.get.return_value = mock_response

        with pytest.raises(CrawlerBlockedException, match=str(status_code)):
            crawler._fetch_from_104_sync(mock_client, "AI", limit=5, page=1)

    def test_job104_search_api_percent_encodes_non_ascii_referer(self):
        from src.server.services.crawling.clients.job104_client import Job104Crawler

        crawler = Job104Crawler()
        mock_client = MagicMock()
        mock_response = MagicMock(status_code=200, headers={"content-type": "application/json"}, json=lambda: {"data": []})
        mock_client.get.return_value = mock_response

        crawler._fetch_from_104_sync(mock_client, "AI系統整合", limit=5, page=1)
        sent_headers = mock_client.get.call_args.kwargs["headers"]
        sent_headers["Referer"].encode("latin-1")
        assert "AI%E7%B3%BB%E7%B5%B1%E6%95%B4%E5%90%88" in sent_headers["Referer"]
