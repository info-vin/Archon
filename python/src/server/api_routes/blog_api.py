from fastapi import APIRouter, Depends, HTTPException, status

from ..models.blog import BlogPostResponse
from ..services.blog_service import BlogService

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
