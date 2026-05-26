import os
import sys
from dotenv import dotenv_values
from supabase import create_client, Client

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
env_vars = dotenv_values(env_path)

url = env_vars.get("SUPABASE_URL")
key = env_vars.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Missing Supabase credentials")
    sys.exit(1)

supabase: Client = create_client(url, key)

print("🔍 Checking archon_settings for old model names...")
response = supabase.table("archon_settings").select("*").execute()

found_issues = False
for row in response.data:
    val = row.get("value")
    if isinstance(val, str) and "gemini-3.1-flash-lite-preview" in val:
        new_val = val.replace("gemini-3.1-flash-lite-preview", "gemini-3.1-flash-lite")
        print(f"  ⚠️ Found in key '{row['key']}': {val} -> Updating to {new_val}")
        supabase.table("archon_settings").update({"value": new_val}).eq("key", row["key"]).execute()
        found_issues = True
        
if not found_issues:
    print("✅ No obsolete model names found in archon_settings.")
else:
    print("✅ Database updated successfully.")
