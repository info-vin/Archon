
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth.dependencies import requires_permission
from ..auth.permissions import CONTENT_PUBLISH, CONTENT_REJECT
from ..models.blog import BlogPostResponse, CreateBlogPostRequest, UpdateBlogPostRequest
from ..services.blog_service import BlogService

router = APIRouter(prefix="/api/blogs", tags=["blog"])


def get_blog_service() -> Any:
    return BlogService()


@router.get("", response_model=list[BlogPostResponse])
async def get_blog_posts(service: BlogService = Depends(get_blog_service)):
    """Get all blog posts. Public access."""
    success, result = await service.list_posts()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error", "Failed to fetch blog posts")
        )
    return result.get("posts", [])


@router.get("/{post_id}", response_model=BlogPostResponse)
async def get_blog_post(post_id: str, service: BlogService = Depends(get_blog_service)):
    """Get a single blog post by ID. Public access."""
    success, result = await service.get_post(post_id)
    if not success:
        if result.get("error") == "Post not found.":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error", "Failed to fetch blog post")
        )
    return result.get("post")


@router.post("", response_model=BlogPostResponse)
async def create_blog_post(
    request: CreateBlogPostRequest,
    current_user: dict = Depends(requires_permission(CONTENT_PUBLISH)),
    service: BlogService = Depends(get_blog_service),
):
    """Create a new blog post. Requires CONTENT_PUBLISH permission."""
    post_data = request.model_dump(mode="json", exclude={"id"})
    success, result = await service.create_post(post_data)
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result.get("post")


@router.patch("/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: str,
    request: UpdateBlogPostRequest,
    current_user: dict = Depends(requires_permission(CONTENT_PUBLISH)),
    service: BlogService = Depends(get_blog_service),
):
    """Update an existing blog post. Requires CONTENT_PUBLISH permission."""
    update_data = request.model_dump(mode="json", exclude_unset=True)
    success, result = await service.update_post(post_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result.get("post")


@router.patch("/{post_id}/status")
async def update_blog_post_status(
    post_id: str,
    request: dict,
    current_user: dict = Depends(requires_permission(CONTENT_PUBLISH)),
    service: BlogService = Depends(get_blog_service),
):
    """Update the status of an existing blog post. Requires CONTENT_PUBLISH permission."""
    status_val = request.get("status")
    if not status_val:
        raise HTTPException(status_code=400, detail="Status value is required.")

    success, result = await service.update_post(post_id, {"status": status_val})
    if not success:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return {"message": "Status updated successfully"}


@router.delete("/{post_id}", status_code=204)
async def delete_blog_post(
    post_id: str,
    current_user: dict = Depends(requires_permission(CONTENT_REJECT)),
    service: BlogService = Depends(get_blog_service),
):
    """Delete a blog post. Requires CONTENT_REJECT permission."""
    success, result = await service.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return None
