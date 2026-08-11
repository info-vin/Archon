# python/src/server/models/blog.py

from datetime import datetime

from pydantic import BaseModel, Field


class BlogPostBase(BaseModel):
    title: str
    excerpt: str | None = None
    content: str
    author_name: str | None = Field(None, alias="authorName")
    publish_date: datetime | None = Field(None, alias="publishDate")
    image_url: str | None = Field(None, alias="imageUrl")
    status: str = "draft"
    review_notes: str | None = Field(None, alias="reviewNotes")
    ai_score: int | None = Field(None, alias="aiScore")
    generation_metadata: dict | None = Field(default_factory=dict, alias="generationMetadata")

    class Config:
        populate_by_name = True
        from_attributes = True
        alias_generator = None  # Ensure explicit aliases are prioritized


class CreateBlogPostRequest(BlogPostBase):
    pass


class UpdateBlogPostRequest(BaseModel):
    title: str | None = None
    excerpt: str | None = None
    content: str | None = None
    author_name: str | None = Field(None, alias="authorName")
    publish_date: datetime | None = Field(None, alias="publishDate")
    image_url: str | None = Field(None, alias="imageUrl")
    status: str | None = None
    review_notes: str | None = Field(None, alias="reviewNotes")
    ai_score: int | None = Field(None, alias="aiScore")
    generation_metadata: dict | None = Field(None, alias="generationMetadata")


class UpdateBlogPostStatusRequest(BaseModel):
    status: str


class BlogPostStatusResponse(BaseModel):
    message: str


class BlogPostResponse(BlogPostBase):
    id: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")
