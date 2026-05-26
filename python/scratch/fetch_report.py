import os
import requests
from dotenv import load_dotenv

load_dotenv('.env')

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

response = requests.get(
    f"{url}/rest/v1/archon_tasks?title=like.*[Daily Report] Executive Summary*&order=created_at.desc&limit=1",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    if data:
        print(data[0]['description'])
    else:
        print("No reports found")
else:
    print(f"Error: {response.status_code} - {response.text}")
