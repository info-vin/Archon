import requests
import os
from dotenv import load_dotenv

# Load env from possible path levels to ensure credentials exist
for p in [".env", "python/.env", "../.env", "../python/.env"]:
    if os.path.exists(p):
        load_dotenv(p)

def setup():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not set.")
        return

    h = {'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}

    # Clean up RUCKUS leads to prevent duplicate key constraint violations during Bob's test
    try:
        res = requests.delete(f'{url}/rest/v1/leads?company_name=eq.RUCKUS Networks', headers=h)
        print(f"Cleaned up existing RUCKUS Networks leads: {res.status_code}")
    except Exception as e:
        print(f"Error cleaning up RUCKUS leads: {e}")
