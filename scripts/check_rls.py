import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("SUPABASE_DB_SESSION_URL") or os.getenv("SUPABASE_DB_URL")
if not db_url:
    print("❌ 錯誤：找不到 SUPABASE_DB_URL 環境變數。請確認您是在正確的終端機環境中執行。")
    exit(1)

tables_to_check = [
    'archon_agents',
    'archon_roles_permissions',
    'archon_agent_tools',
    'archon_role_agents',
    'archon_workflow_flows'
]

print("🔍 開始檢查遠端資料庫 (Supabase) 的 RLS 狀態...")

try:
    conn = psycopg2.connect(db_url)
    with conn.cursor() as cur:
        all_passed = True
        for table in tables_to_check:
            # Check if RLS is enabled
            cur.execute(f"SELECT relrowsecurity FROM pg_class WHERE relname = '{table}';")
            res = cur.fetchone()
            rls_enabled = res[0] if res else False
            
            # Check if policies exist
            cur.execute(f"SELECT policyname FROM pg_policies WHERE tablename = '{table}';")
            policies = [p[0] for p in cur.fetchall()]
            
            status_icon = "✅" if rls_enabled else "❌"
            print(f"{status_icon} Table: {table}")
            print(f"    - RLS Enabled: {rls_enabled}")
            print(f"    - Policies: {policies if policies else 'None'}")
            
            if not rls_enabled:
                all_passed = False

        print("\n===============================")
        if all_passed:
            print("🎉 驗證通過！所有指定的動態 Agent 設定表皆已成功啟用 RLS。")
        else:
            print("⚠️ 驗證失敗：部分表格尚未啟用 RLS，請確認 SQL 腳本是否完整執行。")
        print("===============================\n")

except Exception as e:
    print(f"❌ 連線或查詢時發生錯誤: {e}")
