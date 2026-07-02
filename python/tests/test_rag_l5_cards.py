from unittest.mock import MagicMock, patch

import pytest

from src.server.services.rag_service import RagService


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    # Mock for RPC calls
    client.rpc.return_value.execute.return_value.data = []
    return client


class TestRagL5Cards:
    """Test L5 RAG Cards (MRL & GraphRAG) functionalities"""

    @pytest.mark.asyncio
    async def test_mrl_truncate_dim(self, mock_supabase):
        """Test hybrid_search properly passes truncate_dim down to RPC"""
        # Mock embedding return to avoid network call
        with patch.object(RagService, "get_hf_embedding", return_value=[0.1] * 768):
            with patch("src.server.services.rag_service.get_supabase_client", return_value=mock_supabase):

                # Mock successful return
                mock_response = MagicMock()
                mock_response.data = [{"id": 1, "content": "MRL Content", "similarity": 0.95}]
                mock_supabase.rpc.return_value.execute.return_value = mock_response

                results = await RagService.hybrid_search(
                    query="test MRL",
                    match_count=5,
                    truncate_dim=256
                )

                assert len(results) == 1
                assert results[0]["content"] == "MRL Content"

                # Verify that RPC was called with truncate_dim=256
                mock_supabase.rpc.assert_called_once()
                call_args = mock_supabase.rpc.call_args
                rpc_name = call_args[0][0]
                rpc_params = call_args[0][1]

                assert rpc_name == "hybrid_match_chunks"
                assert rpc_params["truncate_dim"] == 256
                assert "query_embedding" in rpc_params

    @pytest.mark.asyncio
    async def test_graphrag_reasoning(self, mock_supabase):
        """Test graph_search properly calls graph_reasoning_n_hop"""
        with patch("src.server.services.rag_service.get_supabase_client", return_value=mock_supabase):
            # Mock successful return
            mock_response = MagicMock()
            mock_response.data = [
                {"path": "Godot -> GDScript -> MemoryLeak", "hop_count": 2, "final_entity": "MemoryLeak"}
            ]
            mock_supabase.rpc.return_value.execute.return_value = mock_response

            results = await RagService.graph_search(
                start_entity_name="Godot",
                max_hops=2
            )

            assert len(results) == 1
            assert results[0]["final_entity"] == "MemoryLeak"
            assert results[0]["hop_count"] == 2

            # Verify RPC call
            mock_supabase.rpc.assert_called_once()
            call_args = mock_supabase.rpc.call_args
            rpc_name = call_args[0][0]
            rpc_params = call_args[0][1]

            assert rpc_name == "graph_reasoning_n_hop"
            assert rpc_params["start_entity_name"] == "Godot"
            assert rpc_params["max_hops"] == 2
