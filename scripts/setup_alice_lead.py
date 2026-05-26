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

    # 1. Find lead and isolate the queue by updating other new/pending leads to shortlisted
    try:
        # Move other new/pending leads to shortlisted so only RUCKUS is new
        requests.patch(f'{url}/rest/v1/leads?status=in.(new,pending)&company_name=not.like.*RUCKUS*', json={'status': 'shortlisted'}, headers=h)
        print("Isolated new/pending leads queue.")
        leads = requests.get(f'{url}/rest/v1/leads?company_name=like.*RUCKUS*', headers=h).json()
    except Exception as e:
        print(f"Error querying/isolating leads: {e}")
        leads = []


    import datetime
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if leads:
        lead_id = leads[0]['id']
        # Reset to new and update created_at to now to ensure it is at the top of the swipe card queue
        requests.patch(f'{url}/rest/v1/leads?id=eq.{lead_id}', json={'status': 'new', 'created_at': now_str}, headers=h)
        print(f"Lead {lead_id} updated to new with updated created_at.")
    else:
        # Insert a new lead if none exists
        new_lead = {
            "company_name": "RUCKUS Networks",
            "job_title": "Wireless System Engineer",
            "description_snippet": "Hiring for Wireless System Engineer. Experience with Ruckus Access Points preferred.",
            "source_job_url": "https://example.com/ruckus",
            "status": "new",
            "created_at": now_str,
            "identified_need": "- **技術棧**: Ruckus APs, Wi-Fi 6, CCNA.\n- **痛點預測**: 需要專業無線網路部署與疑難排解技能。"
        }
        try:
            res = requests.post(f'{url}/rest/v1/leads', json=new_lead, headers=h)
            if res.status_code in [200, 201]:
                print("Mock RUCKUS lead created.")
            else:
                print(f"Failed to create mock RUCKUS lead: {res.text}")
        except Exception as e:
            print(f"Error inserting mock lead: {e}")
