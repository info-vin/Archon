from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.server.main import app
from src.server.services.migration_service import PendingMigration as ServicePendingMigration


@pytest.mark.asyncio
async def test_get_pending_migrations_route():
    mock_pending = [
        ServicePendingMigration(
            version="0.2.2",
            name="001_initial",
            sql_content="CREATE TABLE test (id INT);",
            file_path="migration/0.2.2/001_initial.sql",
        )
    ]
    with patch("src.server.api_routes.migration_api.migration_service.get_pending_migrations", new_callable=AsyncMock) as mock_get_pending:
        mock_get_pending.return_value = mock_pending
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/migrations/pending")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["version"] == "0.2.2"
            assert data[0]["name"] == "001_initial"
            assert data[0]["sql_content"] == "CREATE TABLE test (id INT);"
            assert data[0]["file_path"] == "migration/0.2.2/001_initial.sql"
            assert "checksum" in data[0]
