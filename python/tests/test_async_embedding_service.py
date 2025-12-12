"""
Comprehensive Tests for Async Embedding Service

Tests all aspects of the async embedding service after sync function removal.
Covers both success and error scenarios with thorough edge case testing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest

from src.server.services.embeddings.embedding_exceptions import (
    EmbeddingAPIError,
)
from src.server.services.embeddings.embedding_service import (
    EmbeddingBatchResult,
    create_embedding,
    create_embeddings_batch,
)


class AsyncContextManager:
    """Helper class for properly mocking async context managers"""

    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestAsyncEmbeddingService:
    """Test suite for async embedding service functions"""

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for testing"""
        mock_client = MagicMock()
        mock_embeddings = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3] + [0.0] * 1533)  # 1536 dimensions
        ]
        mock_embeddings.create = AsyncMock(return_value=mock_response)
        mock_client.embeddings = mock_embeddings
        return mock_client

    @pytest.fixture
    def mock_threading_service(self):
        """Mock threading service for testing"""
        mock_service = MagicMock()
        # Create a proper async context manager
        rate_limit_ctx = AsyncContextManager(None)
        mock_service.rate_limited_operation.return_value = rate_limit_ctx
        return mock_service

    @pytest.mark.asyncio
    async def test_create_embedding_success(self, mock_llm_client, mock_threading_service):
        """Test successful single embedding creation"""
        # 1. Setup mock provider configs
        primary_config = {"provider": "openai", "embedding_model": "text-embedding-3-small", "api_key": "key-ok"}
        mock_get_configs = AsyncMock(return_value=[primary_config])
        mock_create_client = AsyncMock(return_value=mock_llm_client)

        with patch("src.server.services.embeddings.embedding_service.get_threading_service", return_value=mock_threading_service), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_embedding_provider_configs", mock_get_configs), \
             patch("src.server.services.embeddings.embedding_service.create_embedding_client", mock_create_client), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_credentials_by_category", AsyncMock(return_value={"EMBEDDING_BATCH_SIZE": "10"})):

            result = await create_embedding("test text")

            # Verify the result
            assert len(result) == 1536
            assert result[0] == 0.1
            assert result[1] == 0.2
            assert result[2] == 0.3

            # Verify API was called correctly
            mock_llm_client.embeddings.create.assert_called_once()
            mock_create_client.assert_awaited_once_with(primary_config)

    @pytest.mark.asyncio
    async def test_create_embedding_empty_text(self, mock_llm_client, mock_threading_service):
        """Test embedding creation with empty text"""
        primary_config = {"provider": "openai", "embedding_model": "text-embedding-3-small", "api_key": "key-ok"}
        mock_get_configs = AsyncMock(return_value=[primary_config])
        mock_create_client = AsyncMock(return_value=mock_llm_client)

        with patch("src.server.services.embeddings.embedding_service.get_threading_service", return_value=mock_threading_service), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_embedding_provider_configs", mock_get_configs), \
             patch("src.server.services.embeddings.embedding_service.create_embedding_client", mock_create_client), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_credentials_by_category", AsyncMock(return_value={"EMBEDDING_BATCH_SIZE": "10"})):

            result = await create_embedding("")

            # Should still work with empty text
            assert len(result) == 1536
            mock_llm_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_embedding_api_error_raises_exception(self, mock_threading_service):
        """Test embedding creation with API error - should raise exception"""
        # Setup client to raise an error
        mock_client = MagicMock()
        mock_client.embeddings.create = AsyncMock(side_effect=Exception("API Error"))
        mock_client.aclose = AsyncMock()

        primary_config = {"provider": "openai", "embedding_model": "text-embedding-3-small", "api_key": "key-ok"}
        mock_get_configs = AsyncMock(return_value=[primary_config])
        mock_create_client = AsyncMock(return_value=mock_client)

        with patch("src.server.services.embeddings.embedding_service.get_threading_service", return_value=mock_threading_service), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_embedding_provider_configs", mock_get_configs), \
             patch("src.server.services.embeddings.embedding_service.create_embedding_client", mock_create_client), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_credentials_by_category", AsyncMock(return_value={"EMBEDDING_BATCH_SIZE": "10"})):

            # Should raise exception now instead of returning zero embeddings
            with pytest.raises(EmbeddingAPIError):
                await create_embedding("test text")

    @pytest.mark.asyncio
    async def test_create_embeddings_batch_success(self, mock_llm_client, mock_threading_service):
        """Test successful batch embedding creation"""
        # Setup mock response for multiple embeddings
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3] + [0.0] * 1533),
            MagicMock(embedding=[0.4, 0.5, 0.6] + [0.0] * 1533),
        ]
        mock_llm_client.embeddings.create = AsyncMock(return_value=mock_response)

        primary_config = {"provider": "openai", "embedding_model": "text-embedding-3-small", "api_key": "key-ok"}
        mock_get_configs = AsyncMock(return_value=[primary_config])
        mock_create_client = AsyncMock(return_value=mock_llm_client)


        with patch("src.server.services.embeddings.embedding_service.get_threading_service", return_value=mock_threading_service), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_embedding_provider_configs", mock_get_configs), \
             patch("src.server.services.embeddings.embedding_service.create_embedding_client", mock_create_client), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_credentials_by_category", AsyncMock(return_value={"EMBEDDING_BATCH_SIZE": "10"})):

            result = await create_embeddings_batch(["text1", "text2"])

            # Verify the result is EmbeddingBatchResult
            assert isinstance(result, EmbeddingBatchResult)
            assert result.success_count == 2
            assert result.failure_count == 0
            assert len(result.embeddings) == 2
            assert len(result.embeddings[0]) == 1536
            assert len(result.embeddings[1]) == 1536
            assert result.embeddings[0][0] == 0.1
            assert result.embeddings[1][0] == 0.4

            mock_llm_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_embeddings_batch_empty_list(self):
        """Test batch embedding with empty list"""
        result = await create_embeddings_batch([])
        assert isinstance(result, EmbeddingBatchResult)
        assert result.success_count == 0
        assert result.failure_count == 0
        assert result.embeddings == []

    @pytest.mark.asyncio
    async def test_create_embeddings_batch_rate_limit_error(self, mock_threading_service):
        """Test batch embedding with rate limit error"""
        # Setup client to raise rate limit error (not quota)
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        # Create a proper RateLimitError with required attributes
        error = openai.RateLimitError(
            "Rate limit exceeded",
            response=MagicMock(),
            body={"error": {"message": "Rate limit exceeded"}},
        )
        mock_client.embeddings.create = AsyncMock(side_effect=error)

        primary_config = {"provider": "openai", "embedding_model": "text-embedding-3-small", "api_key": "key-ok"}
        mock_get_configs = AsyncMock(return_value=[primary_config])
        mock_create_client = AsyncMock(return_value=mock_client)

        with patch("src.server.services.embeddings.embedding_service.get_threading_service", return_value=mock_threading_service), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_embedding_provider_configs", mock_get_configs), \
             patch("src.server.services.embeddings.embedding_service.create_embedding_client", mock_create_client), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_credentials_by_category", AsyncMock(return_value={"EMBEDDING_BATCH_SIZE": "10"})):

            result = await create_embeddings_batch(["text1", "text2"])

            # After the logic fix, a RateLimitError will be re-raised to the provider level.
            # Since there's only one provider and it fails, the final result will contain the failures.
            assert isinstance(result, EmbeddingBatchResult)
            assert result.success_count == 0
            assert result.failure_count == 2
            assert len(result.embeddings) == 0
            assert len(result.failed_items) == 2

    @pytest.mark.asyncio
    async def test_create_embeddings_batch_quota_exhausted(self, mock_threading_service):
        """Test batch embedding with quota exhausted error"""
        # Setup client to raise quota exhausted error
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        error = openai.RateLimitError(
            "insufficient_quota",
            response=MagicMock(),
            body={"error": {"message": "insufficient_quota"}},
        )
        mock_client.embeddings.create = AsyncMock(side_effect=error)
        
        primary_config = {"provider": "openai", "embedding_model": "text-embedding-3-small", "api_key": "key-ok"}
        mock_get_configs = AsyncMock(return_value=[primary_config])
        mock_create_client = AsyncMock(return_value=mock_client)

        with patch("src.server.services.embeddings.embedding_service.get_threading_service", return_value=mock_threading_service), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_embedding_provider_configs", mock_get_configs), \
             patch("src.server.services.embeddings.embedding_service.create_embedding_client", mock_create_client), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_credentials_by_category", AsyncMock(return_value={"EMBEDDING_BATCH_SIZE": "10"})):

            # Mock progress callback
            progress_callback = AsyncMock()

            result = await create_embeddings_batch(
                ["text1", "text2"], progress_callback=progress_callback
            )

            # A quota error is a provider-level failure. With only one provider, this will result in a failure.
            assert isinstance(result, EmbeddingBatchResult)
            assert result.success_count == 0
            assert result.failure_count == 2
            assert len(result.embeddings) == 0
            assert len(result.failed_items) == 2
            # The specific error message is now wrapped, so we check for the presence of 'quota'
            assert any("quota" in item["error"].lower() for item in result.failed_items)


    @pytest.mark.asyncio
    async def test_create_embeddings_batch_with_progress_callback(
        self, mock_llm_client, mock_threading_service
    ):
        """Test batch embedding with progress callback"""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_llm_client.embeddings.create = AsyncMock(return_value=mock_response)

        primary_config = {"provider": "openai", "embedding_model": "text-embedding-3-small", "api_key": "key-ok"}
        mock_get_configs = AsyncMock(return_value=[primary_config])
        mock_create_client = AsyncMock(return_value=mock_llm_client)

        with patch("src.server.services.embeddings.embedding_service.get_threading_service", return_value=mock_threading_service), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_embedding_provider_configs", mock_get_configs), \
             patch("src.server.services.embeddings.embedding_service.create_embedding_client", mock_create_client), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_credentials_by_category", AsyncMock(return_value={"EMBEDDING_BATCH_SIZE": "1"})):

            # Mock progress callback
            progress_callback = AsyncMock()

            result = await create_embeddings_batch(
                ["text1"], progress_callback=progress_callback
            )

            # Verify result
            assert isinstance(result, EmbeddingBatchResult)
            assert result.success_count == 1

            # Verify progress callback was called
            progress_callback.assert_called()



    @pytest.mark.asyncio
    async def test_create_embeddings_batch_large_batch_splitting(
        self, mock_llm_client, mock_threading_service
    ):
        """Test that large batches are properly split according to batch size settings"""
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536) for _ in range(2)
        ]  # 2 embeddings per call
        mock_llm_client.embeddings.create = AsyncMock(return_value=mock_response)

        primary_config = {"provider": "openai", "embedding_model": "text-embedding-3-small", "api_key": "key-ok"}
        mock_get_configs = AsyncMock(return_value=[primary_config])
        mock_create_client = AsyncMock(return_value=mock_llm_client)

        with patch("src.server.services.embeddings.embedding_service.get_threading_service", return_value=mock_threading_service), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_embedding_provider_configs", mock_get_configs), \
             patch("src.server.services.embeddings.embedding_service.create_embedding_client", mock_create_client), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_credentials_by_category", AsyncMock(return_value={"EMBEDDING_BATCH_SIZE": "2"})):

            # Test with 5 texts (should require 3 API calls: 2+2+1)
            texts = ["text1", "text2", "text3", "text4", "text5"]
            result = await create_embeddings_batch(texts)

            # Should have made 3 API calls due to batching
            assert mock_llm_client.embeddings.create.call_count == 3

            # Result should be EmbeddingBatchResult
            assert isinstance(result, EmbeddingBatchResult)
            # Should have 5 embeddings total (for 5 input texts)
            assert result.success_count == 5
            assert len(result.embeddings) == 5
            assert result.texts_processed == texts

    @pytest.mark.asyncio
    async def test_create_embeddings_batch_with_failover(self, mock_threading_service):
        """Test that the batch creation fails over to a secondary provider."""

        # 1. Setup mock provider configs
        primary_config = {"provider": "primary-fail", "embedding_model": "model-fail", "api_key": "key-fail", "base_url": None}
        secondary_config = {"provider": "secondary-success", "embedding_model": "model-success", "api_key": "key-success", "base_url": None}

        # 2. Mock the new functions
        mock_get_configs = AsyncMock(return_value=[primary_config, secondary_config])

        # Mock client that will be returned by the successful provider
        mock_success_client = MagicMock()
        mock_success_embeddings = MagicMock()
        mock_success_response = MagicMock()
        mock_success_response.data = [
            MagicMock(embedding=[0.1]*1536),
            MagicMock(embedding=[0.2]*1536)
        ]
        mock_success_embeddings.create = AsyncMock(return_value=mock_success_response)
        mock_success_client.embeddings = mock_success_embeddings
        mock_success_client.aclose = AsyncMock()

        # This client will be returned for the failing provider
        mock_fail_client = MagicMock()
        mock_fail_client.embeddings.create = AsyncMock(side_effect=openai.AuthenticationError(message="Invalid API Key", response=MagicMock(), body=None))
        mock_fail_client.aclose = AsyncMock()

        # Stateful side effect for creating clients
        async def create_client_side_effect(config):
            if config["provider"] == "primary-fail":
                return mock_fail_client
            elif config["provider"] == "secondary-success":
                return mock_success_client
            return MagicMock()

        mock_create_client = AsyncMock(side_effect=create_client_side_effect)

        with patch("src.server.services.embeddings.embedding_service.get_threading_service", return_value=mock_threading_service), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_embedding_provider_configs", mock_get_configs), \
             patch("src.server.services.embeddings.embedding_service.create_embedding_client", mock_create_client), \
             patch("src.server.services.embeddings.embedding_service.credential_service.get_credentials_by_category", AsyncMock(return_value={"EMBEDDING_BATCH_SIZE": "10"})):

            # 3. Execute the function
            texts_to_embed = ["text1", "text2"]
            result = await create_embeddings_batch(texts_to_embed)

            # 4. Assertions
            assert result.success_count == 2
            assert result.failure_count == 0
            assert len(result.embeddings) == 2

            # Check that config fetching was called
            mock_get_configs.assert_awaited_once()

            # Check that client creation was attempted for both providers
            assert mock_create_client.call_count == 2
            mock_create_client.assert_any_await(primary_config)
            mock_create_client.assert_any_await(secondary_config)

            # Check that the failing client was used and then the successful one
            mock_fail_client.embeddings.create.assert_awaited_once()
            mock_success_client.embeddings.create.assert_awaited_once()

            # Check clients were closed
            mock_fail_client.aclose.assert_awaited_once()
            mock_success_client.aclose.assert_awaited_once()
