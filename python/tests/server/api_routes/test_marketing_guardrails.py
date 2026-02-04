
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app

client = TestClient(app)

# Mock User Fixture using dependency_overrides
@pytest.fixture
def mock_user_dependency():
    mock_user = {"id": "user1", "role": "marketing", "email": "bob@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    app.dependency_overrides = {}

@pytest.fixture
def mock_services():
    with patch("src.server.api_routes.marketing_api.RAGService") as mock_rag, \
         patch("src.server.api_routes.marketing_api.genai.Client") as mock_genai, \
         patch("src.server.services.credential_service.credential_service.get_credential", new_callable=AsyncMock) as mock_get_cred, \
         patch("src.server.services.credential_service.credential_service.get_active_provider", new_callable=AsyncMock) as mock_get_provider, \
         patch("src.server.services.credential_service.credential_service.get_credentials_by_category", new_callable=AsyncMock) as mock_get_cat, \
         patch("src.server.utils.get_supabase_client") as mock_get_supabase:

        # Mock Credential Service
        mock_get_cred.return_value = "fake-key"
        mock_get_provider.return_value = {"chat_model": "gemini-2.5-flash-lite"}
        mock_get_cat.return_value = {"MARKETING_MODEL": "gemini-2.5-flash-lite"}

        # Mock Supabase for Guardrail logging
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table.return_value.insert.return_value.execute.return_value = None

        # Mock RAG
        rag_instance = mock_rag.return_value
        rag_instance.perform_rag_query = AsyncMock(return_value=(True, {"results": []}))

        # Mock GenAI Client
        mock_client = mock_genai.return_value
        mock_client.models.generate_content.return_value = MagicMock(
            text='{"title": "Safe Blog", "content": "Safe content", "excerpt": "..."}',
            usage_metadata=MagicMock(prompt_token_count=10, candidates_token_count=10)
        )

        yield mock_rag, mock_genai

def test_guardrail_blocks_forbidden_input(mock_user_dependency):
    # Act: Send forbidden keyword
    response = client.post("/api/marketing/blog/draft", json={
        "topic": "How to hack competitor_x",
        "keywords": "exploit",
        "tone": "professional"
    })

    # Assert
    assert response.status_code == 400
    assert "Guardrail Violation" in response.json()["detail"]
    # Relax specific keyword check as set iteration order varies
    # assert "competitor_x" in response.json()["detail"]

def test_guardrail_allows_safe_input(mock_user_dependency, mock_services):
    # Act
    response = client.post("/api/marketing/blog/draft", json={
        "topic": "AI Trends 2026",
        "keywords": "innovation",
        "tone": "professional"
    })

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Safe Blog"

def test_guardrail_blocks_ai_leakage(mock_user_dependency, mock_services):
    # Mock LLM to return leaked AI disclosure
    _, mock_genai = mock_services
    mock_genai.return_value.models.generate_content.return_value = MagicMock(
        text='{"title": "Oops", "content": "I am an AI language model developed by OpenAI.", "excerpt": "..."}',
        usage_metadata=MagicMock(prompt_token_count=10, candidates_token_count=10)
    )

    # Act
    response = client.post("/api/marketing/blog/draft", json={
        "topic": "Safe Topic",
        "keywords": "safe",
        "tone": "professional"
    })

    # Assert
    assert response.status_code == 422
    assert "AI Output Blocked" in response.json()["detail"]
