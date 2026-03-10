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
            "excerpt": "案例一：AI 助您輕鬆完成行銷素材，從文案到視覺一鍵搞定。",
            "content": "案例一內容...",
            "author_name": "Archon 團隊",
            "publish_date": "2025-08-29T10:00:00Z",
            "image_url": "https://picsum.photos/seed/usecase-1/600/400",
            "status": "published"
        },
        {
            "id": "post-2",
            "title": "案例二：從技術支援到知識庫建立的自動化流程",
            "excerpt": "案例二：從技術支援到知識庫建立的自動化流程，提升團隊解決效率。",
            "content": "案例二內容...",
            "author_name": "Archon 團隊",
            "publish_date": "2025-08-28T14:30:00Z",
            "image_url": "https://picsum.photos/seed/usecase-2/600/400",
            "status": "published"
        },
        {
            "id": "post-3",
            "title": "案例三：業務開發與客戶拜訪的智能規劃",
            "excerpt": "案例三：業務開發與客戶拜訪的智能規劃，優化每日行程。",
            "content": "案例三內容...",
            "author_name": "Archon 團隊",
            "publish_date": "2025-08-27T09:00:00Z",
            "image_url": "https://picsum.photos/seed/usecase-3/600/400",
            "status": "published"
        },
        {
            "id": "post-4",
            "title": "案例四：跨國團隊的非同步協作實踐",
            "excerpt": "案例四：如何利用 AI 消除時差障礙，達成 24/7 專案推進。",
            "content": "案例四內容...",
            "author_name": "Archon 團隊",
            "publish_date": "2025-08-26T11:00:00Z",
            "image_url": "https://picsum.photos/seed/usecase-4/600/400",
            "status": "published"
        },
        {
            "id": "post-5",
            "title": "案例五：企業級 RAG 系統的安全性與隱私保護",
            "excerpt": "案例五：深度探討如何在導入 LLM 的同時確保內部資料不外洩。",
            "content": "案例五內容...",
            "author_name": "Archon 團隊",
            "publish_date": "2025-08-25T16:00:00Z",
            "image_url": "https://picsum.photos/seed/usecase-5/600/400",
            "status": "published"
        }
    ]
    
    print(f"Seeding {len(posts)} blog posts...")
    for post in posts:
        res = supabase.table("blog_posts").upsert(post).execute()
        print(f"Upserted {post['id']}")

if __name__ == "__main__":
    seed()
