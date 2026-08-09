import os
import json
import time
import urllib.request
import urllib.error

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '../../.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    os.environ['GEMINI_API_KEY'] = line.strip().split('=', 1)[1]

def call_gemini(model, prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            latency = time.time() - start_time
            return {"status": 200, "latency": latency}
    except urllib.error.HTTPError as e:
        latency = time.time() - start_time
        return {"status": e.code, "latency": latency, "error": str(e)}
    except Exception as e:
        latency = time.time() - start_time
        return {"status": 500, "latency": latency, "error": str(e)}

def run_scenario(name, requests_count, model):
    print(f"\n🚀 Running Scenario: {name} ({requests_count} requests)")
    print("-" * 50)
    
    success_count = 0
    total_time = 0.0
    rate_limited = False
    
    scenario_start = time.time()
    for i in range(requests_count):
        print(f"  [Req {i+1}/{requests_count}] Sending to {model}...")
        res = call_gemini(model, f"Reply with exactly one word: Test {name} {i}")
        
        if res["status"] == 200:
            print(f"    ✅ Success | Latency: {res['latency']:.2f}s")
            success_count += 1
            total_time += res['latency']
        elif res["status"] == 429:
            print(f"    ❌ RATE LIMIT (429) | Latency: {res['latency']:.2f}s")
            rate_limited = True
            break
        else:
            print(f"    ❌ Error {res['status']}: {res.get('error')}")
            break
            
        time.sleep(0.1) # Small gap between requests
        
    scenario_time = time.time() - scenario_start
    print(f"  Result: {success_count}/{requests_count} successful")
    print(f"  Total Scenario Time: {scenario_time:.2f}s")
    if rate_limited:
        print("  ⚠️ SCENARIO FAILED DUE TO RATE LIMITING (429 Too Many Requests)")
    else:
        print("  ✅ SCENARIO COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    load_env()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env")
        exit(1)
        
    model = "models/gemini-3.5-flash-lite"
    print(f"Using Model: {model}")
    
    # Scenario A: RAG (8 requests)
    run_scenario("A. RAG 文件上傳 (Document Agent)", 8, model)
    
    # Scenario C: Self Healing (3 requests)
    run_scenario("C. 自動化與自我修復 (Self Healing)", 3, model)
    
    # Scenario B: Team Debugging (5 requests)
    run_scenario("B. 團隊除錯討論 (Supervisor + DevBot)", 5, model)
