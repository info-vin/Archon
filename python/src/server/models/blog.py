# python/src/server/models/blog.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BlogPostBase(BaseModel):
    title: str
    excerpt: Optional[str] = None
    content: str
    author_name: Optional[str] = Field(None, alias='authorName')
    publish_date: Optional[datetime] = Field(None, alias='publishDate')
    image_url: Optional[str] = Field(None, alias='imageUrl')

    class Config:
        populate_by_name = True
        from_attributes = True

class CreateBlogPostRequest(BlogPostBase):
    pass

class UpdateBlogPostRequest(BaseModel):
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    author_name: Optional[str] = Field(None, alias='authorName')
    publish_date: Optional[datetime] = Field(None, alias='publishDate')
    image_url: Optional[str] = Field(None, alias='imageUrl')

class BlogPostResponse(BlogPostBase):
    id: str
    created_at: datetime = Field(alias='createdAt')
    updated_at: Optional[datetime] = Field(None, alias='updatedAt')