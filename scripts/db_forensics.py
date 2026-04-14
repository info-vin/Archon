import os
import json
from src.server.utils import get_supabase_client

def run_audit():
    sb = get_supabase_client()
    print("--- 物理數據審計開始 ---")
    
    # 1. Check gemini_logs
    try:
        res = sb.table("gemini_logs").select("*").order("created_at", desc=True).limit(1).execute()
        print(f"✅ [gemini_logs]: 存在且包含 {len(res.data)} 筆最新數據")
        if res.data:
            print(f"   最新內容: {json.dumps(res.data[0], indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ [gemini_logs]: 不存在或錯誤 - {str(e)}")

    # 2. Check archon_logs
    try:
        res = sb.table("archon_logs").select("*").order("created_at", desc=True).limit(1).execute()
        print(f"✅ [archon_logs]: 存在且包含 {len(res.data)} 筆最新數據")
    except Exception as e:
        print(f"❌ [archon_logs]: 不存在或錯誤 - {str(e)}")

    # 3. Check MARKETING_MODEL in Seed
    try:
        res = sb.table("archon_settings").select("value").eq("key", "MARKETING_MODEL").execute()
        print(f"✅ [MARKETING_MODEL]: 資料庫現狀 = {res.data[0]['value'] if res.data else 'MISSING'}")
    except Exception as e:
        print(f"❌ [MARKETING_MODEL]: 查詢失敗 - {str(e)}")

run_audit()
