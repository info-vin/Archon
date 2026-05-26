import os

import requests
from dotenv import load_dotenv

load_dotenv('.env')

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')

headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

response = requests.get(
    f"{url}/rest/v1/knowledge_items?select=id,title,source&limit=100",
    headers=headers
)
if response.status_code == 200:
    for item in response.json():
        if '.mp4' in str(item.get('source', '')) or '.webm' in str(item.get('source', '')) or 'video' in str(item.get('title', '')).lower():
            print(item)
