import asyncio
import httpx
import random
import time
import re
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

# --- 配置區 ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
]

TMP_DIR = Path(".gemini/tmp")
TMP_DIR.mkdir(parents=True, exist_ok=True)

class JobData(BaseModel):
    title: str
    company: str
    real_id: str | None = None
    url: str | None = None
    description_len: int = 0
    status: str = "Pending"
    error_msg: str | None = None

class CrawlerReport(BaseModel):
    timestamp: str
    keyword: str
    total_found: int
    processed: int
    success_count: int
    fail_count: int
    jobs: list[JobData] = []

class CrawlerTestRunner:
    def __init__(self, keyword: str, limit: int, verbose: bool):
        self.keyword = keyword
        self.limit = limit
        self.verbose = verbose
        self.base_headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest"
        }
        self.report = CrawlerReport(
            timestamp=datetime.now().isoformat(),
            keyword=keyword,
            total_found=0,
            processed=0,
            success_count=0,
            fail_count=0
        )

    def _get_random_ua(self):
        return random.choice(USER_AGENTS)

    def _save_error_snapshot(self, content: str, prefix: str):
        """保存錯誤快照以便除錯"""
        filename = TMP_DIR / f"crawler_error_{prefix}_{int(time.time())}.html"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            if self.verbose:
                print(f"  📸 Error snapshot saved to: {filename}")
        except Exception as e:
            print(f"  ⚠️ Failed to save snapshot: {e}")

    async def run(self):
        print(f"🚀 [CrawlerTest] Starting... Keyword='{self.keyword}', Limit={self.limit}")
        
        # 使用 Session 保持 Cookies
        headers = self.base_headers.copy()
        headers["User-Agent"] = self._get_random_ua()
        headers["Referer"] = "https://www.104.com.tw/jobs/search/"

        async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
            
            # --- Phase 1: Search List ---
            search_url = "https://www.104.com.tw/jobs/search/api/jobs"
            params = {
                "ro": "0", "kwop": "7", "keyword": self.keyword, 
                "expansionType": "area,spec,com,job,wf,wktm",
                "order": "1", "asc": "0", "page": "1", "mode": "s", "jobsource": "2018indexpoc"
            }
            
            try:
                if self.verbose: print(f"📡 Fetching list from {search_url}...")
                resp = await client.get(search_url, params=params)
                
                if resp.status_code != 200:
                    print(f"❌ List Fetch Failed (Status: {resp.status_code})")
                    self._save_error_snapshot(resp.text, "list_fail")
                    return False

                data = resp.json().get("data", [])
                self.report.total_found = len(data)
                
                if not data:
                    print("⚠️ No jobs found.")
                    return True # Empty but successful technically

                print(f"✅ List fetched. Total: {len(data)}. Processing top {self.limit}...")
                
                # --- Phase 2: Process Details ---
                target_jobs = data[:self.limit]
                self.report.processed = len(target_jobs)

                for i, item in enumerate(target_jobs):
                    job_entry = JobData(
                        title=item.get("jobName", "Unknown"),
                        company=item.get("custName", "Unknown")
                    )
                    
                    # ID Extraction Logic
                    raw_link = item.get("link", {}).get("job", "")
                    real_id = None
                    if "/job/" in raw_link:
                        try:
                            real_id = raw_link.split("?")[0].split("/job/")[1]
                        except:
                            pass
                    
                    job_entry.real_id = real_id
                    job_entry.url = f"https://www.104.com.tw/job/{real_id}" if real_id else raw_link

                    if not real_id:
                        job_entry.status = "Skipped (No ID)"
                        self.report.jobs.append(job_entry)
                        self.report.fail_count += 1
                        continue

                    # Throttling
                    if i > 0:
                        delay = random.uniform(1.5, 3.0)
                        if self.verbose: print(f"⏳ Waiting {delay:.2f}s...")
                        await asyncio.sleep(delay)

                    # Fetch Detail
                    ajax_url = f"https://www.104.com.tw/job/ajax/content/{real_id}"
                    detail_headers = headers.copy()
                    detail_headers["Referer"] = job_entry.url
                    
                    if self.verbose: print(f"📡 Fetching details for {real_id}...")
                    
                    try:
                        d_resp = await client.get(ajax_url, headers=detail_headers)
                        if d_resp.status_code == 200:
                            d_data = d_resp.json()
                            content = d_data.get("data", {}).get("jobDetail", {}).get("jobDescription", "")
                            job_entry.description_len = len(content)
                            if content:
                                job_entry.status = "Success"
                                self.report.success_count += 1
                            else:
                                job_entry.status = "Empty Content"
                                self.report.fail_count += 1
                        else:
                            job_entry.status = f"Failed ({d_resp.status_code})"
                            job_entry.error_msg = f"HTTP {d_resp.status_code}"
                            self._save_error_snapshot(d_resp.text, f"detail_{real_id}")
                            self.report.fail_count += 1
                    except Exception as e:
                        job_entry.status = "Error"
                        job_entry.error_msg = str(e)
                        self.report.fail_count += 1
                    
                    self.report.jobs.append(job_entry)

            except Exception as e:
                print(f"❌ Critical Error: {e}")
                return False

        return True

    def print_summary(self):
        print("\n" + "="*80)
        print(f"📊 CRAWLER REPORT | Success Rate: {self.report.success_count}/{self.report.processed}")
        print("-" * 80)
        print(f"{ 'ID':<8} | {'Company':<20} | {'Status':<15} | {'Content Len'}")
        print("-" * 80)
        for job in self.report.jobs:
            comp = (job.company[:18] + "..") if len(job.company) > 20 else job.company
            rid = job.real_id if job.real_id else "N/A"
            print(f"{rid:<8} | {comp:<20} | {job.status:<15} | {job.description_len}")
        print("="*80)

    def save_report(self, path: str):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.report.model_dump_json(indent=2))
            print(f"📁 Report saved to: {path}")
        except Exception as e:
            print(f"⚠️ Failed to save report: {e}")

async def main():
    parser = argparse.ArgumentParser(description="104 Crawler Reliability Test")
    parser.add_argument("--keyword", default="python", help="Search keyword")
    parser.add_argument("--limit", type=int, default=5, help="Number of jobs to fetch")
    parser.add_argument("--output", default="crawler_report.json", help="Path to save JSON report")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    runner = CrawlerTestRunner(args.keyword, args.limit, args.verbose)
    success = await runner.run()
    
    runner.print_summary()
    runner.save_report(args.output)
    
    # CI Integration: Fail if success rate < 80% (and we processed something)
    if runner.report.processed > 0:
        rate = runner.report.success_count / runner.report.processed
        if rate < 0.8:
            print(f"❌ Success rate ({rate:.1%}) below threshold (80%). Failing CI.")
            sys.exit(1)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
