# python/tests/server/api_routes/test_knowledge_api_blog.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

@pytest.fixture
def client():
    # We need to import the app inside the fixture to ensure the mock patches are applied first
    from src.server.main import app
    return TestClient(app)

# A dictionary for a sample blog post to be reused, ensuring all fields are present
# These are Python model field names, Pydantic will handle aliasing to camelCase
sample_post = {
    "id": "post-1",
    "title": "Test Post",
    "excerpt": "This is a test excerpt.",
    "content": "This is the full content of the test post.",
    "author_name": "Jules",
    "image_url": "http://example.com/image.png",
    "created_at": "2025-10-08T12:00:00+00:00",
    "updated_at": "2025-10-08T12:00:00+00:00",
}

@patch('src.server.api_routes.knowledge_api.BlogService')
def test_list_blog_posts_success(MockBlogService, client):
    """Test successfully listing blog posts."""
    # Arrange
    mock_instance = MockBlogService.return_value
    mock_instance.list_posts = AsyncMock(return_value=(True, {"posts": [sample_post]}))

    # Act
    response = client.get("/api/blogs")

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 1
    assert json_response[0]['title'] == 'Test Post'
    assert json_response[0]['authorName'] == 'Jules' # Check aliasing
    mock_instance.list_posts.assert_awaited_once()

@patch('src.server.api_routes.knowledge_api.BlogService')
def test_get_blog_post_success(MockBlogService, client):
    """Test successfully getting a single blog post."""
    # Arrange
    mock_instance = MockBlogService.return_value
    mock_instance.get_post = AsyncMock(return_value=(True, {"post": sample_post}))

    # Act
    response = client.get("/api/blogs/post-1")

    # Assert
    assert response.status_code == 200
    assert response.json()['title'] == 'Test Post'
    assert response.json()['content'] == sample_post['content']
    mock_instance.get_post.assert_awaited_once_with('post-1')

@patch('src.server.api_routes.knowledge_api.BlogService')
def test_get_blog_post_not_found(MockBlogService, client):
    """Test getting a non-existent blog post."""
    # Arrange
    mock_instance = MockBlogService.return_value
    mock_instance.get_post = AsyncMock(return_value=(False, {"error": "Post not found"}))

    # Act
    response = client.get("/api/blogs/post-dne")

    # Assert
    assert response.status_code == 404
    mock_instance.get_post.assert_awaited_once_with('post-dne')


# --- RBAC Tests ---

@pytest.mark.parametrize("role, expected_status", [
    ("SYSTEM_ADMIN", 200),
    ("User", 403),
    (None, 403)
])
@patch('src.server.api_routes.knowledge_api.BlogService')
def test_create_blog_post_rbac(MockBlogService, client, role, expected_status):
    """Test create blog post endpoint with different user roles."""
    # Arrange
    headers = {"X-User-Role": role} if role is not None else {}
    # This is the data we send in the request body
    post_data = {"title": "New Post", "content": "Some content", "author_name": "Jules"}

    # This is what we expect the service to be called with after Pydantic model processing
    expected_call_data = {
        "title": "New Post",
        "excerpt": None,
        "content": "Some content",
        "author_name": "Jules",
        "publish_date": None,
        "image_url": None,
    }

    mock_instance = MockBlogService.return_value
    # Ensure the mock return value has all required fields for the response model
    created_post = {**sample_post, **post_data, "id": "new-post-id"}
    mock_instance.create_post = AsyncMock(return_value=(True, {"post": created_post}))

    # Act
    response = client.post("/api/blogs", json=post_data, headers=headers)

    # Assert
    assert response.status_code == expected_status
    if expected_status == 200:
        # Assert that the service method was called with the data processed by the Pydantic model
        mock_instance.create_post.assert_awaited_once_with(expected_call_data)
        assert response.json()["id"] == "new-post-id"
    else:
        mock_instance.create_post.assert_not_awaited()


@pytest.mark.parametrize("role, expected_status", [
    ("SYSTEM_ADMIN", 200),
    ("User", 403),
    (None, 403)
])
@patch('src.server.api_routes.knowledge_api.BlogService')
def test_update_blog_post_rbac(MockBlogService, client, role, expected_status):
    """Test update blog post endpoint with different user roles."""
    # Arrange
    headers = {"X-User-Role": role} if role is not None else {}
    update_data = {"title": "Updated Title"}

    mock_instance = MockBlogService.return_value
    updated_post = {**sample_post, **update_data}
    mock_instance.update_post = AsyncMock(return_value=(True, {"post": updated_post}))

    # Act
    response = client.put("/api/blogs/post-1", json=update_data, headers=headers)

    # Assert
    assert response.status_code == expected_status
    if expected_status == 200:
        mock_instance.update_post.assert_awaited_once_with("post-1", update_data)
        assert response.json()["title"] == "Updated Title"
    else:
        mock_instance.update_post.assert_not_awaited()


@pytest.mark.parametrize("role, expected_status", [
    ("SYSTEM_ADMIN", 204),
    ("User", 403),
    (None, 403)
])
@patch('src.server.api_routes.knowledge_api.BlogService')
def test_delete_blog_post_rbac(MockBlogService, client, role, expected_status):
    """Test delete blog post endpoint with different user roles."""
    # Arrange
    headers = {"X-User-Role": role} if role is not None else {}
    mock_instance = MockBlogService.return_value
    mock_instance.delete_post = AsyncMock(return_value=(True, {}))

    # Act
    response = client.delete("/api/blogs/post-1", headers=headers)

    # Assert
    assert response.status_code == expected_status
    if expected_status == 204:
        mock_instance.delete_post.assert_awaited_once_with("post-1")
    else:
        mock_instance.delete_post.assert_not_awaited()