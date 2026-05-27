import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure python folder is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

for p in [".env", "python/.env", "../.env", "../python/.env"]:
    if os.path.exists(p):
        load_dotenv(p)

from src.server.utils import get_supabase_client

async def run_setup():
    print("🧪 Running Charlie Approval Pre-Hook...")
    supabase = get_supabase_client()
    
    blog_title = "Charlie Verification Blog Post"
    
    # 1. Clean up existing Charlie Verification blog posts
    try:
        supabase.table("blog_posts").delete().eq("title", blog_title).execute()
        print(f"Cleaned existing '{blog_title}' records.")
    except Exception as e:
        print(f"Error cleaning existing records: {e}")
        
    # 2. Insert a fresh blog post pending review
    import datetime
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    mock_blog_post = {
        "title": blog_title,
        "excerpt": "This is a verification post waiting for Charlie's approval or rejection.",
        "content": "This is the draft content that Bob submitted for review. It needs to be reviewed by Charlie.",
        "author_name": "Bob",
        "status": "review",
        "target_brand": "Archon",
        "created_at": now_str,
        "updated_at": now_str
    }
    
    try:
        supabase.table("blog_posts").insert(mock_blog_post).execute()
        print(f"Mock blog post '{blog_title}' inserted directly with status=review.")
    except Exception as e:
        print(f"Error seeding mock blog post: {e}")

async def setup():
    await run_setup()

if __name__ == "__main__":
    asyncio.run(run_setup())
