from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.search.rag_service import RAGService


@pytest.fixture
def mock_genai_client():
    with patch("src.server.services.search.rag_service.genai.Client") as mock:
        client_instance = mock.return_value

        # Mocking GenerateContentResponse
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "This is a web search summary."
        mock_candidate.content.parts = [mock_part]

        # Mocking Grounding Metadata
        mock_chunk = MagicMock()
        mock_chunk.web.uri = "https://example.com"
        mock_candidate.grounding_metadata.grounding_chunks = [mock_chunk]

        mock_response.candidates = [mock_candidate]

        client_instance.models.generate_content.return_value = mock_response
        yield client_instance


@pytest.fixture
def mock_librarian():
    # Patch where the class is defined, not where it is imported locally
    with patch("src.server.services.librarian_service.LibrarianService") as mock:
        instance = mock.return_value
        instance.archive_web_research = AsyncMock(return_value="web-source-123")
        yield instance


@pytest.fixture
def mock_credential_service():
    # Patch the service instance in credential_service module
    with patch("src.server.services.credential_service.credential_service") as mock:
        mock.get_credential = AsyncMock(return_value="fake-api-key")
        yield mock


@pytest.fixture
def mock_base_dependencies():
    with (
        patch("src.server.services.search.rag_service.get_supabase_client"),
        patch("src.server.services.search.rag_service.BaseSearchStrategy"),
        patch("src.server.services.search.rag_service.HybridSearchStrategy"),
        patch("src.server.services.search.rag_service.AgenticRAGStrategy"),
        patch("src.server.services.search.rag_service.create_embedding", new_callable=AsyncMock) as mock_embed,
    ):
        mock_embed.return_value = [0.1, 0.2, 0.3]
        yield


@pytest.mark.asyncio
async def test_perform_web_research_success(
    mock_base_dependencies, mock_genai_client, mock_librarian, mock_credential_service
):
    service = RAGService()

    content, source_id = await service.perform_web_research("latest ai trends")

    assert content == "This is a web search summary."
    assert source_id == "web-source-123"

    # Verify GenAI call
    mock_genai_client.models.generate_content.assert_called_once()

    # Verify Librarian archive
    mock_librarian.archive_web_research.assert_called_once()
    args = mock_librarian.archive_web_research.call_args[0]
    assert args[0] == "latest ai trends"
    assert args[1] == "This is a web search summary."
    assert args[2] == ["https://example.com"]


@pytest.mark.asyncio
async def test_perform_rag_query_with_web_research(
    mock_base_dependencies, mock_genai_client, mock_librarian, mock_credential_service
):
    service = RAGService()

    # Mock base search strategy returns
    service.base_strategy.vector_search = AsyncMock(
        return_value=[{"id": "doc-1", "content": "Internal doc", "similarity": 0.8}]
    )

    # Execute with enable_web_research=True in metadata
    result_success, result_data = await service.perform_rag_query(
        query="latest trends", filter_metadata={"enable_web_research": True}
    )

    assert result_success is True
    results = result_data["results"]

    # Should have web result first (due to prepend)
    assert len(results) >= 2
    assert results[0]["metadata"]["type"] == "web_research"
    assert results[0]["content"] == "This is a web search summary."

    # Check execution path
    # Mock Librarian should have been called
    mock_librarian.archive_web_research.assert_called_once()
