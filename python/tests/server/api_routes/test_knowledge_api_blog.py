# python/tests/server/api_routes/test_knowledge_api_blog.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Mock the supabase client before app initialization
@pytest.fixture(autouse=True)
def mock_supabase_client():
    with patch('src.server.utils.get_supabase_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client

@pytest.fixture
def client():
    from src.server.main import app
    return TestClient(app)


def test_list_blog_posts_success(client, mock_supabase_client):
    """Test successfully listing blog posts."""
    # Arrange
    mock_data = [{'id': 'post-1', 'title': 'Test Post'}]
    mock_supabase_client.table.return_value.select.return_value.order.return_value.execute.return_value.data = mock_data

    # Act
    response = client.get("/api/blogs")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['title'] == 'Test Post'

def test_get_blog_post_success(client, mock_supabase_client):
    """Test successfully getting a single blog post."""
    # Arrange
    mock_data = {'id': 'post-1', 'title': 'Test Post', 'content': 'Content'}
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = mock_data

    # Act
    response = client.get("/api/blogs/post-1")

    # Assert
    assert response.status_code == 200
    assert response.json()['title'] == 'Test Post'

def test_get_blog_post_not_found(client, mock_supabase_client):
    """Test getting a non-existent blog post."""
    # Arrange
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

    # Act
    response = client.get("/api/blogs/post-dne")

    # Assert
    assert response.status_code == 404

# --- RBAC Tests ---

@pytest.mark.parametrize("role, expected_status", [
    ("SYSTEM_ADMIN", 200),
    ("User", 403),
    (None, 403)
])
def test_create_blog_post_rbac(client, mock_supabase_client, role, expected_status):
    """Test create blog post endpoint with different user roles."""
    # Arrange
    headers = {"X-User-Role": role} if role else {}
    post_data = {"title": "New Post", "content": "Some content"}
    mock_supabase_client.table.return_value.insert.return_value.select.return_value.single.return_value.execute.return_value.data = {"id": "new-post", **post_data}

    # Act
    response = client.post("/api/blogs", json=post_data, headers=headers)

    # Assert
    assert response.status_code == expected_status

@pytest.mark.parametrize("role, expected_status", [
    ("SYSTEM_ADMIN", 200),
    ("User", 403),
    (None, 403)
])
def test_update_blog_post_rbac(client, mock_supabase_client, role, expected_status):
    """Test update blog post endpoint with different user roles."""
    # Arrange
    headers = {"X-User-Role": role} if role else {}
    update_data = {"title": "Updated Title"}
    mock_supabase_client.table.return_value.update.return_value.eq.return_value.select.return_value.single.return_value.execute.return_value.data = {"id": "post-1", **update_data}

    # Act
    response = client.put("/api/blogs/post-1", json=update_data, headers=headers)

    # Assert
    assert response.status_code == expected_status

@pytest.mark.parametrize("role, expected_status", [
    ("SYSTEM_ADMIN", 204),
    ("User", 403),
    (None, 403)
])
def test_delete_blog_post_rbac(client, mock_supabase_client, role, expected_status):
    """Test delete blog post endpoint with different user roles."""
    # Arrange
    headers = {"X-User-Role": role} if role else {}
    # Mock successful deletion
    mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value.error = None

    # Act
    response = client.delete("/api/blogs/post-1", headers=headers)

    # Assert
    assert response.status_code == expected_status
