import os
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_key(name, key):
    if not key:
        print(f"❌ {name} is not set.")
        return
    
    # 測試 Gemini 1.5 Flash 穩定版 API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents":[{"parts":[{"text":"ping"}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"✅ {name} (ends in ...{key[-4:]}) is VALID.")
        else:
            print(f"❌ {name} (ends in ...{key[-4:]}) is INVALID. Status: {response.status_code}")
            print(f"   Reason: {response.text}")
    except Exception as e:
        print(f"❌ {name} verification error: {e}")

print("🔍 Verifying API Keys from .env...")
verify_key("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))
verify_key("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
