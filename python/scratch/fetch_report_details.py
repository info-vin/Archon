import os

import requests
from dotenv import load_dotenv

load_dotenv('.env')

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}'
}

response = requests.get(
    f"{url}/rest/v1/archon_tasks?title=like.*[Daily Report] Executive Summary*&order=created_at.desc&limit=1",
    headers=headers
)

if response.status_code == 200 and response.json():
    print(response.json()[0]['description'])
