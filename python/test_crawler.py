import asyncio
from src.server.services.job_board_service import JobBoardService

async def test_crawler():
    print("Testing 104 Crawler...")
    jobs = await JobBoardService.search_jobs("python", limit=5)
    for i, job in enumerate(jobs):
        print(f"[{i+1}] {job.company} - {job.title} (Source: {job.source})")
        if job.source == "mock":
            print("  ⚠️ WARNING: Mock data detected!")
        else:
            print(f"  ✅ Real data: {job.url}")

if __name__ == "__main__":
    asyncio.run(test_crawler())
