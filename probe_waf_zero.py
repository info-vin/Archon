import time
from curl_cffi import requests as cffi_requests

keywords = ["Python", "AI", "React", "Node", "Golang", "Java", "C++", "C#", "Ruby", "PHP"]
url = "https://www.104.com.tw/jobs/search/?keyword="

def probe(delay):
    print(f"Testing delay: {delay}s")
    session = cffi_requests.Session(impersonate="chrome110")
    for kw in keywords:
        try:
            res = session.get(url + kw, timeout=10)
            if res.status_code == 200:
                print(f"[{kw}] OK (200)")
            elif res.status_code == 403:
                print(f"[{kw}] BLOCKED (403)")
                return False
            else:
                print(f"[{kw}] HTTP {res.status_code}")
        except Exception as e:
            print(f"[{kw}] Error: {e}")
            return False
        time.sleep(delay)
    return True

print("Starting 0s probe...")
probe(0)
