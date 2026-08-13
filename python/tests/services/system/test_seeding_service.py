from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.system.seeding_service import ALLOWED_SEED_EXTENSIONS, DEFAULT_KNOWLEDGE_TYPE, SeedingService


@pytest.mark.asyncio
async def test_seeding_service_constants():
    # Test that the constants are defined correctly
    assert ".md" in ALLOWED_SEED_EXTENSIONS
    assert ".txt" in ALLOWED_SEED_EXTENSIONS
    assert DEFAULT_KNOWLEDGE_TYPE == "technical"

@pytest.mark.asyncio
@patch("os.path.exists", return_value=True)
@patch("os.walk")
@patch("aiofiles.open")
async def test_seed_knowledge_uses_constants(mock_aiofiles_open, mock_os_walk, mock_exists):
    mock_os_walk.return_value = [("/app/mock", [], ["test.md", "ignore.pdf"])]

    mock_file = AsyncMock()
    mock_file.read.return_value = "Test content"
    mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

    # Mock LibrarianService
    mock_supabase = MagicMock()
    with patch("src.server.services.system.seeding_service.LibrarianService") as MockLibrarian:
        mock_librarian_instance = MockLibrarian.return_value
        mock_librarian_instance.archive_file = AsyncMock()

        service = SeedingService(supabase_client=mock_supabase)
        service.librarian = mock_librarian_instance

        result = await service.seed_knowledge()

        assert result.get("status") == "completed"
        assert result.get("total_files") == 1
        assert result.get("indexed_count") == 1

        mock_librarian_instance.archive_file.assert_called_once_with(
            file_name="test.md",
            content="Test content",
            file_path="/app/mock/test.md",
            knowledge_type=DEFAULT_KNOWLEDGE_TYPE
        )
