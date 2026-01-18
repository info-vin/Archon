
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from python.src.server.services.job_board_service import JobBoardService
from python.src.server.config.logfire_config import configure_logging

async def test_crawl():
    print("🚀 Starting crawler test...")
    configure_logging()
    
    # Use a specific keyword likely to have results
    keyword = "Python Engineer"
    
    try:
        jobs = await JobBoardService.search_jobs(keyword, limit=3)
        print(f"\n✅ Found {len(jobs)} jobs")
        
        for i, job in enumerate(jobs):
            print(f"\n--- Job {i+1} ---")
            print(f"Title: {job.title}")
            print(f"Company: {job.company}")
            print(f"URL: {job.url}")
            print(f"Source: {job.source}")
            
            # Critical Check: Is description_full populated and meaningful?
            desc_len = len(job.description_full) if job.description_full else 0
            print(f"Full Description Length: {desc_len}")
            
            if job.description_full:
                print(f"Preview: {job.description_full[:200]}...")
            else:
                print("❌ WARNING: No full description fetched!")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_crawl())
