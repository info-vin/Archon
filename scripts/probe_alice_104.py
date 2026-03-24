import httpx
import asyncio
import sys

async def run_probe():
    # 物理對齊 JobBoardService 的最新 Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.104.com.tw/jobs/search/",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
        print("🔍 [Probe A1] Sending Pre-warm request to 104 Home...")
        try:
            r1 = await client.get("https://www.104.com.tw/jobs/search/")
            cookies = r1.cookies
            print(f"✅ [Probe A1] Warm-up SUCCESS. Cookies captured: {len(cookies)}")
            
            print("\n🚀 [Probe A1] Sending AJAX Detail request (Critical Path)...")
            # 測試之前報錯的具體職缺 ID
            job_id = "8pws1"
            url = f"https://www.104.com.tw/job/ajax/content/{job_id}"
            
            # 對齊 03/18 歷史實作：動態修改 Referer
            headers["Referer"] = f"https://www.104.com.tw/job/{job_id}"
            
            r2 = await client.get(url, headers=headers)
            print(f"📊 [Probe A1] API Status: {r2.status_code}")
            print(f"📄 [Probe A1] Content-Type: {r2.headers.get('Content-Type')}")
            
            if "application/json" in r2.headers.get("Content-Type", ""):
                print("💎 [Probe A1] PHYSICAL REALIZATION SUCCESS: Real JSON data obtained.")
                sys.exit(0)
            else:
                print("🔴 [Probe A1] PHYSICAL FAILURE: WAF intercepted (HTML received).")
                sys.exit(1)
        except Exception as e:
            print(f"💥 [Probe A1] CRASH: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_probe())
