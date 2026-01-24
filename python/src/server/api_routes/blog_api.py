from fastapi import APIRouter, Depends, HTTPException, status

from ..auth.dependencies import get_current_user
from ..models.blog import BlogPostResponse, CreateBlogPostRequest, UpdateBlogPostRequest
from ..services.blog_service import BlogService
from ..services.rbac_service import RBACService

router = APIRouter(prefix="/api/blogs", tags=["blog"])

def get_blog_service():
    return BlogService()

@router.get("", response_model=list[BlogPostResponse])
async def get_blog_posts(service: BlogService = Depends(get_blog_service)):
    """Get all blog posts."""
    success, result = await service.list_posts()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to fetch blog posts")
        )
    return result.get("posts", [])

@router.get("/{post_id}", response_model=BlogPostResponse)
async def get_blog_post(post_id: str, service: BlogService = Depends(get_blog_service)):
    """Get a single blog post by ID."""
    success, result = await service.get_post(post_id)
    if not success:
        if result.get("error") == "Post not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to fetch blog post")
        )
    return result.get("post")

@router.post("", response_model=BlogPostResponse)
async def create_blog_post(
    request: CreateBlogPostRequest,
    current_user: dict = Depends(get_current_user),
    service: BlogService = Depends(get_blog_service)
):
    """Create a new blog post."""
    rbac_service = RBACService()
    user_role = current_user.get("role", "viewer")

    if not rbac_service.can_manage_content(user_role):
        raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to create blog posts.")

    success, result = await service.create_post(request.model_dump())
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result.get("post")

@router.put("/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: str,
    request: UpdateBlogPostRequest,
    current_user: dict = Depends(get_current_user),
    service: BlogService = Depends(get_blog_service)
):
    """Update an existing blog post."""
    rbac_service = RBACService()
    user_role = current_user.get("role", "viewer")

    if not rbac_service.can_manage_content(user_role):
        raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to update blog posts.")

    update_data = request.model_dump(exclude_unset=True)
    success, result = await service.update_post(post_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result.get("post")

@router.delete("/{post_id}", status_code=204)
async def delete_blog_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    service: BlogService = Depends(get_blog_service)
):
    """Delete a blog post."""
    rbac_service = RBACService()
    user_role = current_user.get("role", "viewer")

    if not rbac_service.can_manage_content(user_role):
        raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to delete blog posts.")

    success, result = await service.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return None
