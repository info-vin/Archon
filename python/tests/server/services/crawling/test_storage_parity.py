import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.server.services.crawling.document_storage_operations import DocumentStorageOperations

@pytest.mark.asyncio
async def test_process_and_store_documents_logic():
    """物理驗證模組化後的存儲邏輯是否正確執行分塊與元數據生成"""
    with patch("src.server.services.crawling.document_storage_operations.DocumentStorageService") as mock_storage_service_cls:
        mock_storage = mock_storage_service_cls.return_value
        # 模擬分塊回傳
        mock_storage.smart_chunk_text_async = AsyncMock(return_value=["chunk1", "chunk2"])
        
        ops = DocumentStorageOperations(supabase_client=MagicMock())
        
        # 模擬外部相依函數
        with patch("src.server.services.crawling.document_storage_operations.add_documents_to_supabase", new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {"chunks_stored": 2}
            
            with patch.object(ops, "_create_source_records", new_callable=AsyncMock) as mock_create_src:
                crawl_results = [{"url": "https://test.com/1", "markdown": "content content content"}]
                request = {"knowledge_type": "documentation", "tags": ["test"]}
                
                result = await ops.process_and_store_documents(
                    crawl_results=crawl_results,
                    request=request,
                    crawl_type="single",
                    original_source_id="test-source"
                )
                
                assert result["chunk_count"] == 2
                assert result["source_id"] == "test-source"
                mock_add.assert_called_once()
                print("\n✅ Task B2: Storage Parity Test PASSED.")

if __name__ == "__main__":
    pytest.main([__file__])
