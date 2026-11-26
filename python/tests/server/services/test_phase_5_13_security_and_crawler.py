from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import InvalidToken

from src.server.services.credentials.crypto_utils import CryptoUtils
from src.server.services.credentials.manager import CredentialManager
from src.server.services.scheduler.jobs.crawler_patrol import run_whitelist_crawler_patrol


class TestDualKeyCredentialRotation:
    def test_encrypt_with_dedicated_key_and_decrypt_old_key_fallback(self, monkeypatch):
        old_service_key = "sb_secret_old_service_key_123"
        new_enc_key = "independent_credential_encryption_key_456"

        # 1. Encrypt under old service key only (legacy state before rotation)
        legacy_cfg = SimpleNamespace(
            supabase_service_key=old_service_key,
            credential_encryption_key=None,
            previous_supabase_service_key=None,
        )
        with patch("src.server.config.config.get_config", return_value=legacy_cfg):
            legacy_ciphertext = CryptoUtils.encrypt_value("my-gemini-secret")

        # 2. Rotate SUPABASE_SERVICE_KEY and set CREDENTIAL_ENCRYPTION_KEY + PREVIOUS_SUPABASE_SERVICE_KEY
        rotated_cfg = SimpleNamespace(
            supabase_service_key="sb_secret_brand_new_key_789",
            credential_encryption_key=new_enc_key,
            previous_supabase_service_key=old_service_key,
        )
        with patch("src.server.config.config.get_config", return_value=rotated_cfg):
            # Old ciphertext still decrypts seamlessly via PREVIOUS_SUPABASE_SERVICE_KEY fallback
            assert CryptoUtils.decrypt_value(legacy_ciphertext) == "my-gemini-secret"
            # New encryption uses CREDENTIAL_ENCRYPTION_KEY (independent of SUPABASE_SERVICE_KEY)
            new_ciphertext = CryptoUtils.encrypt_value("my-gemini-secret")
            assert CryptoUtils.decrypt_value(new_ciphertext) == "my-gemini-secret"

        # 3. After SUPABASE_SERVICE_KEY changes again, ciphertext encrypted with CREDENTIAL_ENCRYPTION_KEY still works
        rotated_again_cfg = SimpleNamespace(
            supabase_service_key="sb_secret_another_new_key_999",
            credential_encryption_key=new_enc_key,
            previous_supabase_service_key=None,
        )
        with patch("src.server.config.config.get_config", return_value=rotated_again_cfg):
            assert CryptoUtils.decrypt_value(new_ciphertext) == "my-gemini-secret"
            with pytest.raises(InvalidToken):
                CryptoUtils.decrypt_value(legacy_ciphertext)

    @pytest.mark.asyncio
    async def test_credential_manager_falls_back_to_env_when_decrypt_fails(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "env-fallback-gemini-key")
        mgr = CredentialManager()
        mgr._cache_initialized = True
        mgr._cache["GEMINI_API_KEY"] = {"encrypted_value": "corrupt-or-old-token", "is_encrypted": True}

        with patch.object(CryptoUtils, "decrypt_value", side_effect=InvalidToken("bad key")):
            val = await mgr.get_credential("GEMINI_API_KEY")

        assert val == "env-fallback-gemini-key"


class TestWhitelistCrawlerPatrol:
    @pytest.mark.asyncio
    async def test_crawls_only_due_non_manual_targets(self):
        now = datetime.now(UTC)
        targets = [
            {
                "id": "manual-1",
                "target_url": "https://fate.windada.com/cgi-bin/calendar",
                "max_depth": 2,
                "is_active": True,
                "update_frequency": "manual",
                "last_crawled_at": None,
            },
            {
                "id": "google-due-1",
                "target_url": "https://ai.google.dev/gemini-api/docs/deprecations?hl=zh-tw",
                "max_depth": 5,
                "is_active": True,
                "update_frequency": "bi-weekly",
                "last_crawled_at": None,
            },
            {
                "id": "google-due-2",
                "target_url": "https://ai.google.dev/gemini-api/docs/troubleshooting?hl=zh-tw",
                "max_depth": 5,
                "is_active": True,
                "update_frequency": "bi-weekly",
                "last_crawled_at": (now - timedelta(days=15)).isoformat(),
            },
            {
                "id": "google-recent",
                "target_url": "https://ai.google.dev/gemini-api/docs/recent",
                "max_depth": 5,
                "is_active": True,
                "update_frequency": "bi-weekly",
                "last_crawled_at": (now - timedelta(days=3)).isoformat(),
            },
        ]

        mock_supabase = MagicMock()
        mock_crawler = MagicMock()
        mock_crawler.orchestrate_crawl = AsyncMock(return_value={"success": True})

        logged_events: list[tuple[str, str, str]] = []

        def _capture(job_name: str, phase: str, message: str, details=None, level: str = "INFO", supabase=None) -> None:
            logged_events.append((job_name, phase, level))

        with (
            patch("src.server.services.scheduler.jobs.crawler_patrol.get_supabase_client", return_value=mock_supabase),
            patch("src.server.services.scheduler.jobs.crawler_patrol.BaseRepository") as mock_repo_cls,
            patch("src.server.services.scheduler.jobs.crawler_patrol.log_patrol_event", side_effect=_capture),
            patch("src.server.services.crawling.crawling_service.CrawlingService", return_value=mock_crawler),
        ):
            mock_repo = mock_repo_cls.return_value
            mock_repo.execute_query.side_effect = [
                (True, {"data": targets}),
                (True, {"data": []}),
                (True, {"data": []}),
            ]

            count = await run_whitelist_crawler_patrol()

        assert count == 2
        assert ("whitelist_crawler_patrol", "start", "INFO") in logged_events
        assert ("whitelist_crawler_patrol", "completed", "INFO") in logged_events
        crawled_urls = [call.args[0]["url"] for call in mock_crawler.orchestrate_crawl.call_args_list]
        assert crawled_urls == [
            "https://ai.google.dev/gemini-api/docs/deprecations?hl=zh-tw",
            "https://ai.google.dev/gemini-api/docs/troubleshooting?hl=zh-tw",
        ]

    def test_scheduler_config_alice_auto_fetch_interval_ssot(self):
        from src.server.schemas.settings import SchedulerConfig

        cfg = SchedulerConfig.model_validate({"ALICE_AUTO_FETCH_INTERVAL_HOURS": 6})
        assert cfg.alice_auto_fetch_interval_hours == 6
        assert not hasattr(cfg, "alice_auto_fetch_days")
