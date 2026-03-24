import pytest
from fastapi.testclient import TestClient

from src.server.main import app

client = TestClient(app)

@pytest.mark.parametrize("endpoint", [
    "/api/health",
    "/api/marketing/leads",
    "/api/visit-logs/attendance/status",
    "/api/stats/commander-trends",
    "/api/system/prompts/list",
    "/api/migrations/status"
])
def test_api_endpoints_smoke(endpoint):
    """物理遍歷所有核心 API 端點，驗證基本通訊 (非 404/500)"""
    # 注意：我們只測連通性，所以 401 Unauthorized 也是一種成功的「連通」證明 (代表路由有掛載)
    response = client.get(endpoint)
    assert response.status_code != 404
    assert response.status_code != 500
    print(f"\n✅ Smoke Test: {endpoint} returned {response.status_code}")

if __name__ == "__main__":
    pytest.main([__file__])
