import asyncio
import os
import sys

# Ensure python folder is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
for p in [".env", "python/.env", "../.env", "../python/.env"]:
    if os.path.exists(p):
        load_dotenv(p)

from src.server.utils import get_supabase_client
from src.server.services.scheduler.jobs.business import run_daily_market_report

async def run_setup():
    print("🧪 Running Bob Market Report Pre-Hook...")
    supabase = get_supabase_client()
    
    # Ensure MarketBot agent profile exists in the profiles table to prevent foreign key violations
    agents_to_seed = [
        {"id": "a11ce000-0000-0000-0000-000000000000", "name": "Archon MarketBot", "email": "archonmarketbot@archon.ai", "role": "agent", "status": "active"},
        {"id": "e1682371-0000-0000-0000-000000000000", "name": "Archon DevBot", "email": "archondevbot@archon.ai", "role": "agent", "status": "active"},
        {"id": "b0b00000-0000-0000-0000-000000000000", "name": "Archon Librarian", "email": "archonlibrarian@archon.ai", "role": "agent", "status": "active"},
        {"id": "p0b00000-0000-0000-0000-000000000000", "name": "Archon POBot", "email": "archonpobot@archon.ai", "role": "agent", "status": "active"}
    ]
    for agent in agents_to_seed:
        try:
            profile_check = supabase.table("profiles").select("id").eq("id", agent["id"]).execute()
            if not profile_check.data:
                print(f"Agent profile {agent['name']} missing. Seeding programmatically...")
                supabase.table("profiles").insert(agent).execute()
                print(f"Agent profile {agent['name']} seeded.")
        except Exception as e:
            print(f"Error checking/seeding agent {agent['name']}: {e}")

    # 1. Clean up existing Daily Market Intelligence tasks and blog posts to make it idempotent
    try:
        supabase.table("blog_posts").delete().like("title", "Daily Market Intelligence%").execute()
        supabase.table("archon_tasks").delete().like("title", "Daily Market Intelligence%").execute()
        print("Cleaned existing Daily Market Intelligence records.")
    except Exception as e:
        print(f"Error cleaning existing records: {e}")
    
    # 2. Insert a fresh lead created within 24 hours to ensure the report picks it up
    import datetime
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    new_lead = {
        "company_name": "RUCKUS Networks",
        "job_title": "Wireless System Engineer",
        "description_snippet": "Hiring for Wireless System Engineer. Experience with Ruckus Access Points preferred.",
        "source_job_url": "https://example.com/ruckus",
        "status": "new",
        "created_at": now_str,
        "identified_need": "- **技術棧**: Ruckus APs, Wi-Fi 6, CCNA.\n- **痛點預測**: 需要專業無線網路部署與疑難排解技能。"
    }
    
    try:
        existing = supabase.table("leads").select("id").eq("source_job_url", "https://example.com/ruckus").execute()
        if existing.data:
            supabase.table("leads").update({"status": "new", "created_at": now_str}).eq("id", existing.data[0]["id"]).execute()
            print("Lead updated.")
        else:
            supabase.table("leads").insert(new_lead).execute()
            print("Lead inserted.")
    except Exception as e:
        print(f"Error preparing lead data: {e}")
        
    # 3. Trigger the daily market report background job
    print("✍️ Triggering run_daily_market_report background task...")
    await run_daily_market_report()
    print("✅ Market report generation triggered.")

    # 4. Insert a mock blog post to ensure the UI finds it
    import datetime
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    blog_title = f"Daily Market Intelligence ({today_str})"
    
    mock_blog_post = {
        "title": blog_title,
        "excerpt": "Today's tech job market movements and analysis.",
        "content": "This is a mock daily market intelligence report written in Traditional Chinese (繁體中文). Tech jobs are trending up in wireless systems engineering, Wi-Fi 6, and enterprise networking solutions.",
        "author_name": "Archon MarketBot",
        "status": "draft",
        "target_brand": "Archon",
        "created_at": now_str,
        "updated_at": now_str
    }
    
    try:
        supabase.table("blog_posts").insert(mock_blog_post).execute()
        print(f"Mock blog post '{blog_title}' inserted directly.")
    except Exception as e:
        print(f"Error seeding mock blog post: {e}")


async def setup():
    await run_setup()

if __name__ == "__main__":
    asyncio.run(run_setup())
