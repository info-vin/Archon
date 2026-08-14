import asyncio
from unittest.mock import patch

from src.server.services.crawling.clients.job104_client import Job104Crawler


async def main():
    print("Starting crawler test...")
    # Mock SettingsService to prevent Supabase connection error and simulate DB state
    with patch("src.server.services.crawling.clients.job104_client.SettingsService") as MockSettings:
        instance = MockSettings.return_value
        instance.get_setting.return_value = None  # Mocking DB proxy returning None
        crawler = Job104Crawler()
        try:
            jobs = await asyncio.wait_for(crawler.search_jobs("AI行銷自動化", limit=2), timeout=30)
            print(f"Found {len(jobs)} jobs.")
            for j in jobs:
                print(f"- {j.title}")
        except Exception as e:
            print(f"Exception: {type(e).__name__} - {e}")
    print("Done crawler test.")

if __name__ == "__main__":
    asyncio.run(main())
