from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.librarian.business_archiver import BusinessArchiver, FailureCaseMetadataDTO
from src.server.services.librarian_service import LibrarianService


@pytest.mark.asyncio
async def test_business_archiver_archive_failure_case():
    mock_supabase = MagicMock()
    mock_repo = MagicMock()

    archiver = BusinessArchiver(supabase=mock_supabase, repo=mock_repo)

    metadata: FailureCaseMetadataDTO = {
        "outcome": "failure",
        "reason": "Budget constraints",
        "company": "Acme Corp",
        "job": "Software Engineer",
    }

    with patch("src.server.services.librarian.business_archiver.update_source_info", new_callable=AsyncMock) as mock_update_info, \
         patch("src.server.services.librarian.business_archiver.create_embedding", new_callable=AsyncMock) as mock_embedding:
        mock_embedding.return_value = [0.1, 0.2, 0.3]

        res = await archiver.archive_failure_case(
            content="Sample content",
            reason="Budget constraints",
            company="Acme Corp",
            job_title="Software Engineer",
            metadata=metadata,
        )

        assert res.startswith("fail-acme-corp-")
        mock_update_info.assert_awaited_once()
        mock_repo.insert_crawled_page.assert_called_once()


@pytest.mark.asyncio
async def test_librarian_service_facade():
    mock_supabase = MagicMock()

    with patch("src.server.services.librarian_service.FileArchiver") as mock_file_archiver_cls, \
         patch("src.server.services.librarian_service.WebArchiver") as mock_web_archiver_cls, \
         patch("src.server.services.librarian_service.BusinessArchiver") as mock_business_archiver_cls:

        mock_file_archiver = MagicMock()
        mock_web_archiver = MagicMock()
        mock_business_archiver = MagicMock()

        mock_file_archiver_cls.return_value = mock_file_archiver
        mock_web_archiver_cls.return_value = mock_web_archiver
        mock_business_archiver_cls.return_value = mock_business_archiver

        mock_business_archiver.archive_failure_case = AsyncMock(return_value="fail-id-123")

        service = LibrarianService(supabase=mock_supabase)

        metadata: FailureCaseMetadataDTO = {"outcome": "failure"}
        result = await service.archive_failure_case("content", "reason", "company", "job_title", metadata)

        assert result == "fail-id-123"
        mock_business_archiver.archive_failure_case.assert_awaited_once_with(
            "content", "reason", "company", "job_title", metadata
        )
