import asyncio

from src.server.services.marketing.content_handler import ContentHandler
from src.server.services.marketing.lead_handler import LeadHandler
from src.server.services.scheduler.jobs.business import run_business_sentinel
from src.server.utils import get_supabase_client


async def main():
    print("Testing Business Orchestration...")
    sb = get_supabase_client()

    print("\n--- Test A: Alice Lead Lost ---")
    lead_res = sb.table("leads").insert({"company_name": "Test Lost Company", "job_title": "Engineer"}).execute()
    if lead_res.data:
        lead_id = lead_res.data[0]["id"]
        handler = LeadHandler(sb)
        await handler.update_lead(lead_id, {"status": "LOST", "lost_reason": "Too expensive"})
        # Wait a bit for the background task to complete
        await asyncio.sleep(2)

        pages_res = sb.table("archon_crawled_pages").select("metadata").ilike("metadata->>company", "Test Lost Company").execute()
        if pages_res.data:
            print(f"✅ Alice Test Passed! Found failure analysis page: {pages_res.data[0]}")
        else:
            print("❌ Alice Test Failed. Failure analysis page not found.")

    print("\n--- Test B: Bob Content Rejection ---")
    blog_res = sb.table("blog_posts").insert({"title": "Test Reject Blog", "content": "Test content", "status": "review"}).execute()
    if blog_res.data:
        post_id = blog_res.data[0]["id"]
        handler = ContentHandler(sb)
        await handler.process_approval("blog", post_id, "REJECT", "Tone is wrong.")
        await asyncio.sleep(2)

        doc_res = sb.table("archon_document_versions").select("change_summary").ilike("change_summary", "%Test Reject Blog%").execute()
        if doc_res.data:
            print(f"✅ Bob Test Passed! Found style critique doc version: {doc_res.data[0]}")
        else:
            print("❌ Bob Test Failed. Style critique doc version not found.")

    print("\n--- Test C: Charlie Sentinel & Task ---")
    lead_res2 = sb.table("leads").insert({"company_name": "Test Stale Company", "job_title": "Developer", "status": "new", "updated_at": "2020-01-01T00:00:00Z"}).execute()
    if lead_res2.data:
        # We need to configure the threshold to ensure it triggers
        sb.table("archon_settings").upsert({"key": "STALE_LEAD_THRESHOLD_DAYS", "value": "1"}, on_conflict="key").execute()
        await run_business_sentinel()
        await asyncio.sleep(5)

        tasks_res = sb.table("archon_tasks").select("title, description").ilike("title", "%Test Stale Company%").execute()
        if tasks_res.data:
            print(f"✅ Charlie Test Passed! Found auto-generated task: {tasks_res.data[0]}")
        else:
            print("❌ Charlie Test Failed. Auto-generated task not found.")

if __name__ == "__main__":
    asyncio.run(main())
