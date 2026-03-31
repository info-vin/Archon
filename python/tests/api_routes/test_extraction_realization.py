
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from server.services.extraction_service import ExtractionService

@pytest.mark.asyncio
async def test_extraction_service_realization_logic():
    """
    Physically verifies the extraction logic: 
    Crawl -> LLM Parse -> Persistence.
    """
    schema_id = "test-schema-uuid"
    test_url = "https://example.com/data"
    user_id = "test-mgr-id"
    
    # 1. Setup Mocks
    with patch("server.services.extraction_service.get_supabase_client") as mock_db_factory, \
         patch("server.services.extraction_service.get_crawler") as mock_get_crawler, \
         patch("server.services.llm_provider_service.get_llm_client") as mock_get_llm:
        
        mock_db = MagicMock()
        mock_db_factory.return_value = mock_db
        
        # Mock Schema retrieval
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": schema_id, 
            "name": "Test Realization", 
            "schema_definition": {"fields": [{"name": "price", "type": "number"}]}
        }]

        # Mock Crawler instance
        mock_crawler = AsyncMock()
        mock_get_crawler.return_value = mock_crawler
        mock_crawler.arun.return_value = MagicMock(markdown="The price is 500 dollars.")

        # Mock LLM Client
        mock_llm = AsyncMock()
        mock_get_llm.return_value.__aenter__.return_value = mock_llm
        
        # Concrete class to avoid MagicMock recursion depth issues
        class MockMessage:
            def __init__(self, content):
                self.content = content
                self.tool_calls = None
                self.audio = None
                self.refusal = None
                self.function_call = None

        class MockChoice:
            def __init__(self, content):
                self.message = MockMessage(content)

        mock_response = MagicMock()
        mock_response.choices = [MockChoice('{"price": 500}')]
        mock_llm.chat.completions.create.return_value = mock_response

        # 2. Execute Service Method
        service = ExtractionService(supabase_client=mock_db)
        result = await service.run_extraction(test_url, schema_id, user_id)

        # 3. PHYSICAL ASSERTIONS
        assert result["success"] is True
        assert result["data"]["price"] == 500
        assert result["schema_used"] == "Test Realization"
        
        print("\n✅ Assertion Passed: Extraction Service physical logic verified.")

if __name__ == "__main__":
    import asyncio
    print("\n🚀 STARTING STANDALONE PHYSICAL VERIFICATION...")
    asyncio.run(test_extraction_service_realization_logic())
    print("\n✨ ALL TESTS PASSED!")
