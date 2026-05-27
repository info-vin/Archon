import asyncio
import os
import sys
import datetime
import random
import argparse
import requests
from dotenv import load_dotenv

# Ensure python folder is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load env from possible path levels to ensure credentials exist
for p in [".env", "python/.env", "../.env", "../python/.env"]:
    if os.path.exists(p):
        load_dotenv(p)

from src.server.utils import get_supabase_client

def get_rest_headers():
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }

async def setup_alice():
    print("🧪 Running Alice Lead Pre-Hook...")
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not set.")
        return

    h = get_rest_headers()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        # Move other new/pending leads to shortlisted so only RUCKUS is new
        requests.patch(f'{url}/rest/v1/leads?status=in.(new,pending)&company_name=not.like.*RUCKUS*', json={'status': 'shortlisted'}, headers=h)
        print("Isolated new/pending leads queue.")
        leads = requests.get(f'{url}/rest/v1/leads?company_name=like.*RUCKUS*', headers=h).json()
    except Exception as e:
        print(f"Error querying/isolating leads: {e}")
        leads = []

    if leads:
        lead_id = leads[0]['id']
        requests.patch(f'{url}/rest/v1/leads?id=eq.{lead_id}', json={'status': 'new', 'created_at': now_str}, headers=h)
        print(f"Lead {lead_id} updated to new with updated created_at.")
    else:
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
            res = requests.post(f'{url}/rest/v1/leads', json=new_lead, headers=h)
            if res.status_code in [200, 201]:
                print("Mock RUCKUS lead created.")
            else:
                print(f"Failed to create mock RUCKUS lead: {res.text}")
        except Exception as e:
            print(f"Error inserting mock lead: {e}")

async def setup_bob_pitch():
    print("🧪 Running Bob Pitch Pre-Hook...")
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not set.")
        return

    h = get_rest_headers()
    try:
        res = requests.delete(f'{url}/rest/v1/leads?company_name=eq.RUCKUS Networks', headers=h)
        print(f"Cleaned up existing RUCKUS Networks leads: {res.status_code}")
    except Exception as e:
        print(f"Error cleaning up RUCKUS leads: {e}")

async def setup_bob_report():
    print("🧪 Running Bob Market Report Pre-Hook...")
    from src.server.services.scheduler.jobs.business import run_daily_market_report
    supabase = get_supabase_client()
    
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
                print(f"Agent profile {agent['name']} missing. Seeding...")
                supabase.table("profiles").insert(agent).execute()
                print(f"Agent profile {agent['name']} seeded.")
        except Exception as e:
            print(f"Error checking/seeding agent {agent['name']}: {e}")

    try:
        supabase.table("blog_posts").delete().like("title", "Daily Market Intelligence%").execute()
        supabase.table("archon_tasks").delete().like("title", "Daily Market Intelligence%").execute()
        print("Cleaned existing Daily Market Intelligence records.")
    except Exception as e:
        print(f"Error cleaning existing records: {e}")
    
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
        
    print("✍️ Triggering run_daily_market_report background task...")
    await run_daily_market_report()
    print("✅ Market report generation triggered.")

    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    blog_title = f"Daily Market Intelligence ({today_str})"
    mock_blog_post = {
        "title": blog_title,
        "excerpt": "Today's tech job market movements and analysis.",
        "content": """這是一份針對近期科技就業市場趨勢的深度行銷情報分析報告。

根據我們系統在過去 24 小時內所擷取的大量商機與職缺數據顯示，企業端對於具備無線通訊技術背景的工程師需求正呈現顯著的上升趨勢。特別是在 Wi-Fi 6 標準普及化與 5G 專網建置的雙重驅動下，包含 Ruckus Networks 在內的企業級網路設備商，正積極擴編其無線系統工程與技術支援團隊。

進一步分析這些職缺的技術需求，我們發現單一的硬體維護技能已不足以滿足現代企業的期望。市場目前高度青睞能夠結合雲端控制器 (Cloud Controllers)、軟體定義網路 (SDN) 以及具備基礎 Python 自動化腳本撰寫能力的複合型人才。這暗示著網路基礎設施的部署模式，正從傳統的硬體堆疊迅速轉向高度軟體化與可程式化的智能維運 (AIOps) 模式。

對於我們的行銷與業務開發策略而言，這是一個極佳的切入點。我們應該針對這些正在擴張網路工程團隊的企業，主動推送我們在自動化維運與智慧監控解決方案上的成功案例，以精準命中他們在擴展基礎設施時所面臨的人力與管理痛點。""",
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

async def setup_charlie():
    print("🧪 Running Charlie Approval Pre-Hook...")
    supabase = get_supabase_client()
    blog_title = "Charlie Verification Blog Post"
    
    try:
        supabase.table("blog_posts").delete().eq("title", blog_title).execute()
        print(f"Cleaned existing '{blog_title}' records.")
    except Exception as e:
        print(f"Error cleaning existing records: {e}")
        
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

async def setup_david():
    print("🧪 Running David RBAC Matrix Pre-Hook...")
    supabase = get_supabase_client()
    original_sales_perms = [
        'task:create', 
        'task:read:own', 
        'task:read:team', 
        'task:update:own', 
        'agent:trigger:mkt', 
        'leads:view:all', 
        'leads:view:sales', 
        'stats:view:own'
    ]
    try:
        supabase.table("archon_roles_permissions").update({
            "permissions": original_sales_perms
        }).eq("role", "sales").execute()
        print("Restored sales role permissions to default.")
    except Exception as e:
        print(f"Error resetting sales permissions: {e}")

async def setup_sandbox(level_id: str = "GENERIC_LEVEL", force_clean: bool = True):
    print(f"🧪 [Sandbox] Initializing state for level: {level_id} (force_clean={force_clean})")
    await asyncio.sleep(random.uniform(0.1, 0.5))
    if "L1_STAGE_04" in level_id:
        print(f"🧪 [Sandbox] Routing L1_STAGE_04 to Charlie setup")
        await setup_charlie()
    elif "alice_hunter" in level_id:
        await setup_alice()
    else:
        print(f"🧪 [Sandbox] Generic mock seeding completed for level {level_id}")

async def main():
    parser = argparse.ArgumentParser(description="Archon Persona setup script")
    parser.add_argument("--role", choices=["alice", "bob_pitch", "bob_report", "charlie", "david", "sandbox", "all"], default="all")
    parser.add_argument("--level_id", default="GENERIC_LEVEL")
    parser.add_argument("--force_clean", default="true")
    args = parser.parse_args()

    if args.role == "alice":
        await setup_alice()
    elif args.role == "bob_pitch":
        await setup_bob_pitch()
    elif args.role == "bob_report":
        await setup_bob_report()
    elif args.role == "charlie":
        await setup_charlie()
    elif args.role == "david":
        await setup_david()
    elif args.role == "sandbox":
        await setup_sandbox(args.level_id, args.force_clean.lower() == "true")
    elif args.role == "all":
        await setup_alice()
        await setup_bob_pitch()
        await setup_bob_report()
        await setup_charlie()
        await setup_david()

if __name__ == "__main__":
    asyncio.run(main())
