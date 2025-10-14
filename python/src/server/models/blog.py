# python/src/server/models/blog.py

from datetime import datetime

from pydantic import BaseModel, Field


class BlogPostBase(BaseModel):
    title: str
    excerpt: str | None = None
    content: str
    author_name: str | None = Field(None, alias='authorName')
    publish_date: datetime | None = Field(None, alias='publishDate')
    image_url: str | None = Field(None, alias='imageUrl')

    class Config:
        populate_by_name = True
        from_attributes = True

class CreateBlogPostRequest(BlogPostBase):
    pass

class UpdateBlogPostRequest(BaseModel):
    title: str | None = None
    excerpt: str | None = None
    content: str | None = None
    author_name: str | None = Field(None, alias='authorName')
    publish_date: datetime | None = Field(None, alias='publishDate')
    image_url: str | None = Field(None, alias='imageUrl')

class BlogPostResponse(BlogPostBase):
    id: str
    created_at: datetime = Field(alias='createdAt')
    updated_at: datetime | None = Field(None, alias='updatedAt')
