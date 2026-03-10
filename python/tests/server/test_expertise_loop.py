from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from server.api_routes.marketing_api import get_marketing_service
from server.auth.dependencies import get_current_user
from server.main import app


@pytest.fixture
def client():
    # Force Auth override for Charlie (Manager)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "charlie-id", "role": "manager", "email": "charlie@archon.ai"
    }
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_marketing_approval_triggers_learning(client):
    """
    Bob's Loop: Charlie rejects a blog -> Expertise loop triggers learning.
    """
    # 物理修正：使用 Dependency Override 注入 Mock Service
    mock_svc = MagicMock()
    # process_approval 回傳 bool
    mock_svc.process_approval = AsyncMock(return_value=True)
    app.dependency_overrides[get_marketing_service] = lambda: mock_svc

    # 模擬 Librarian 學習 (這是在 Service 內部被觸發的)
    # 我們這裡驗證 API 是否能成功接收請求並回傳 200
    response = client.post(
        "/api/marketing/approvals/blog/blog-1/reject",
        json={"reviewNotes": "Too many exclamation marks!"}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    # 驗證 Service 是否被呼叫
    mock_svc.process_approval.assert_called_once()
