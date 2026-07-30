import os
import sys
from dotenv import load_dotenv

# Load root .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add python dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'python')))

from src.server.utils import get_supabase_client

def main():
    try:
        supabase = get_supabase_client()
        result = supabase.table("archon_settings").select("key, value").like("key", "MCP_RESTRICTED_%").execute()
        
        if result.data:
            print("✅ Verified: Found the following MCP restricted settings in the database:")
            for item in result.data:
                print(f"  - {item['key']}: {item['value']}")
        else:
            print("❌ Verification Failed: No MCP restricted settings found in the database.")
            
    except Exception as e:
        print(f"❌ Error connecting to Supabase or querying data: {e}")

if __name__ == "__main__":
    main()
