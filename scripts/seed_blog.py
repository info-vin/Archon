"""
Manual Seed Script for Blog Posts
Ensures the blog table has data for UI verification.
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "python"))

from src.server.utils import get_supabase_client

def seed():
    supabase = get_supabase_client()
    
    posts = [
        {
            "id": "post-1",
            "title": "案例一：AI 助您輕鬆完成行銷素材",
            "excerpt": "案例一：AI 助您輕鬆完成行銷素材...",
            "content": "案例一：AI 助您輕鬆完成行銷素材的完整內容...",
            "author_name": "Archon 團隊",
            "publish_date": "2025-08-29T10:00:00Z",
            "image_url": "https://picsum.photos/seed/usecase-1/600/400",
            "status": "published"
        },
        {
            "id": "post-2",
            "title": "案例二：從技術支援到知識庫建立的自動化流程",
            "excerpt": "案例二：從技術支援到知識庫建立的自動化流程...",
            "content": "案例二：從技術支援到知識庫建立的自動化流程的完整內容...",
            "author_name": "Archon 團隊",
            "publish_date": "2025-08-28T14:30:00Z",
            "image_url": "https://picsum.photos/seed/usecase-2/600/400",
            "status": "published"
        },
        {
            "id": "post-3",
            "title": "案例三：業務開發與客戶拜訪的智能規劃",
            "excerpt": "案例三：業務開發與客戶拜訪的智能規劃...",
            "content": "案例三：業務開發與客戶拜訪的智能規劃的完整內容...",
            "author_name": "Archon 團隊",
            "publish_date": "2025-08-27T09:00:00Z",
            "image_url": "https://picsum.photos/seed/usecase-3/600/400",
            "status": "published"
        }
    ]
    
    print(f"Seeding {len(posts)} blog posts...")
    for post in posts:
        res = supabase.table("blog_posts").upsert(post).execute()
        print(f"Upserted {post['id']}: {res.data}")

if __name__ == "__main__":
    seed()
