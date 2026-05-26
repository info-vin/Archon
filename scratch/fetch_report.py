import os, json
from dotenv import dotenv_values
from supabase import create_client

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
env_vars = dotenv_values(env_path)
supabase = create_client(env_vars["SUPABASE_URL"], env_vars["SUPABASE_SERVICE_KEY"])

print("🔍 正在資料庫中尋找剛才產生的報告...")
# 尋找包含 Executive Summary 或是 Report 的最新任務
res = supabase.table("archon_tasks").select("title, description, created_at").ilike("title", "%Executive Summary%").order("created_at", desc=True).limit(1).execute()

if res.data:
    print("\n" + "="*50)
    print(f"📄 報告標題: {res.data[0]['title']}")
    print(f"🕒 建立時間: {res.data[0]['created_at']}")
    print("="*50)
    print(res.data[0]['description'])
    print("="*50)
else:
    print("❌ 找不到報告！")
