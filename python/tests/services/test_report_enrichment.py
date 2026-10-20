from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from src.server.services.report_enrichment_service import ReportEnrichmentService


@patch("src.server.utils.get_supabase_client")
def test_prune_expired_podcast_audio_success(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    now = datetime.now(UTC)
    old_time_1 = (now - timedelta(days=30)).isoformat()
    old_time_2 = (now - timedelta(days=20)).isoformat()
    recent_time = (now - timedelta(days=2)).isoformat()

    mock_files = [
        {"name": "podcast_old_1.wav", "created_at": old_time_1},
        {"name": "podcast_old_2.wav", "created_at": old_time_2},
        {"name": "podcast_recent.wav", "created_at": recent_time},
        {"name": "user_contract.pdf", "created_at": old_time_1},
        {"name": "podcast_no_date.wav", "created_at": None},
        {"name": "not_a_dict"},
    ]

    mock_bucket = MagicMock()
    mock_bucket.list.return_value = mock_files
    mock_bucket.remove.return_value = [{"name": "podcast_old_1.wav"}, {"name": "podcast_old_2.wav"}]
    mock_supabase.storage.from_.return_value = mock_bucket

    pruned = ReportEnrichmentService.prune_expired_podcast_audio(ttl_days=14)

    assert pruned == 2
    mock_bucket.list.assert_called_once()
    mock_bucket.remove.assert_called_once_with(["podcast_old_1.wav", "podcast_old_2.wav"])
    mock_supabase.table.assert_called_with("archon_logs")


@patch("src.server.utils.get_supabase_client")
def test_prune_expired_podcast_audio_empty(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    mock_bucket = MagicMock()
    mock_bucket.list.return_value = []
    mock_supabase.storage.from_.return_value = mock_bucket

    pruned = ReportEnrichmentService.prune_expired_podcast_audio(ttl_days=14)

    assert pruned == 0
    mock_bucket.remove.assert_not_called()


@patch("src.server.utils.get_supabase_client")
def test_prune_expired_podcast_audio_storage_error_handled(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    mock_bucket = MagicMock()
    mock_bucket.list.side_effect = Exception("Storage service unavailable")
    mock_supabase.storage.from_.return_value = mock_bucket

    pruned = ReportEnrichmentService.prune_expired_podcast_audio(ttl_days=14)

    assert pruned == 0
