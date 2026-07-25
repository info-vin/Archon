import time
import requests
from curl_cffi import requests as cffi_requests

keywords = ["Python", "AI", "React", "Node", "Golang"]
url = "https://www.104.com.tw/jobs/search/?keyword="

def probe(delay):
    print(f"Testing delay: {delay}s")
    session = cffi_requests.Session(impersonate="chrome110")
    for kw in keywords[:3]:  # test 3 keywords
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

print("Starting probe...")
if not probe(5):
    print("5s failed, trying 15s...")
    time.sleep(10)
    if not probe(15):
        print("15s failed, trying 30s...")
        time.sleep(10)
        probe(30)
