import sys

def test_httpx():
    print("\n--- Testing HTTPX (Current Codebase Approach) ---")
    import httpx
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.104.com.tw/jobs/search/",
    }
    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as client:
            warmup = client.get("https://www.104.com.tw/jobs/search/?keyword=Python")
            print(f"Warmup status: {warmup.status_code}")
            
            params = {"ro": "0", "kwop": "7", "keyword": "Python", "order": "1", "asc": "0", "page": "1", "mode": "s", "jobsource": "2018indexpoc"}
            headers["Accept"] = "application/json, text/plain, */*"
            headers["X-Requested-With"] = "XMLHttpRequest"
            res = client.get("https://www.104.com.tw/jobs/search/api/jobs", params=params, headers=headers)
            print(f"AJAX API status: {res.status_code}")
            if res.status_code == 200:
                print("Data snippet:", str(res.json())[:100])
    except Exception as e:
        print(f"HTTPX failed: {e}")

def test_curl_cffi():
    print("\n--- Testing curl_cffi (Impersonation Approach) ---")
    try:
        from curl_cffi import requests
        headers = {
            "Referer": "https://www.104.com.tw/jobs/search/",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
        }
        # curl_cffi will automatically handle User-Agent when impersonating Chrome
        session = requests.Session(impersonate="chrome120")
        
        warmup = session.get("https://www.104.com.tw/jobs/search/?keyword=Python")
        print(f"Warmup status: {warmup.status_code}")
        
        params = {"ro": "0", "kwop": "7", "keyword": "Python", "order": "1", "asc": "0", "page": "1", "mode": "s", "jobsource": "2018indexpoc"}
        res = session.get("https://www.104.com.tw/jobs/search/api/jobs", params=params, headers=headers)
        print(f"AJAX API status: {res.status_code}")
        if res.status_code == 200:
            print("Data snippet:", str(res.json())[:100])
    except Exception as e:
        print(f"curl_cffi failed: {e}")

if __name__ == "__main__":
    test_httpx()
    test_curl_cffi()
