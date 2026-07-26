from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import pytest

from server.main import app

client = TestClient(app)

@patch("server.api_routes.extraction_api.ExtractionService")
def test_list_schemas(mock_service_class):
    mock_service = mock_service_class.return_value
    mock_service.list_schemas = AsyncMock(return_value=[
        {"id": "schema-1", "name": "Test Schema", "schema_definition": {}}
    ])

    # Normally we need to mock dependencies like get_current_user/requires_permission
    # We will just verify the service mock is called if we can bypass auth
