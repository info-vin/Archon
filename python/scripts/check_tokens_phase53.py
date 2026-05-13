import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv(".env")
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

def main():
    if not url or not key:
        print("Missing Supabase credentials")
        return

    supabase: Client = create_client(url, key)
    try:
        res = supabase.table("token_usage").select("*").order("created_at", desc=True).limit(5).execute()
        print("--- Recent Token Usage Records ---")
        for row in res.data:
            print(row)
    except Exception as e:
        print(f"Error checking tokens: {e}")

if __name__ == "__main__":
    main()
