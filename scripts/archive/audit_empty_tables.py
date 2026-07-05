import os
import sys
import re
import psycopg2
from collections import defaultdict

# Add search directories
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEARCH_PATHS = [
    os.path.join(WORKSPACE_DIR, "python", "src"),
    os.path.join(WORKSPACE_DIR, "archon-ui-main", "src"),
    os.path.join(WORKSPACE_DIR, "enduser-ui-fe", "src")
]

DB_URL = os.getenv("SUPABASE_DB_SESSION_URL") or os.getenv("SUPABASE_DB_URL")

def count_code_occurrences(table_name: str) -> int:
    """Scan the codebase to count occurrences of a table name."""
    count = 0
    # Clean table name for searching
    clean_name = table_name.replace("public.", "")
    # Check singular forms as well (e.g. tasks -> task)
    singular_name = clean_name[:-1] if clean_name.endswith("s") else clean_name
    
    pattern = re.compile(rf"\b({clean_name}|{singular_name})\b", re.IGNORECASE)
    
    for path in SEARCH_PATHS:
        if not os.path.exists(path):
            continue
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".sql")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            count += len(pattern.findall(content))
                    except Exception:
                        pass
    return count

def run_audit():
    if not DB_URL:
        print("❌ Error: SUPABASE_DB_URL (or SUPABASE_DB_SESSION_URL) not set in environment.")
        sys.exit(1)
        
    print(f"🔍 Connecting to Supabase Database...")
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=5)
        cur = conn.cursor()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
        
    print("📊 Auditing tables structure and usage statistics...")
    
    # 1. Get all base tables in public schema
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    
    # 2. Get execution statistics from pg_stat_user_tables
    cur.execute("""
        SELECT relname, seq_scan, idx_scan, n_tup_ins, n_tup_upd, n_tup_del
        FROM pg_stat_user_tables
        WHERE schemaname = 'public';
    """)
    stats = {row[0]: {
        "seq_scan": row[1],
        "idx_scan": row[2],
        "inserts": row[3],
        "updates": row[4],
        "deletes": row[5]
    } for row in cur.fetchall()}
    
    report_data = []
    
    for table in tables:
        # Get row count
        try:
            cur.execute(f'SELECT COUNT(*) FROM public."{table}"')
            row_count = cur.fetchone()[0]
        except Exception as e:
            row_count = -1
            print(f"⚠️ Error counting rows for {table}: {e}")
            conn.rollback()
            
        t_stats = stats.get(table, {
            "seq_scan": 0, "idx_scan": 0, "inserts": 0, "updates": 0, "deletes": 0
        })
        
        # Scan codebase for references
        code_refs = count_code_occurrences(table)
        
        # Determine status
        if row_count > 0:
            status = "🟢 Active (Has Data)"
        elif code_refs > 0:
            # Check if it's a known empty placeholder table (like ethics_events or audit_logs)
            if table in ["ethics_events", "audit_logs", "archon_document_versions"]:
                status = "🟡 Active Placeholder (0 rows, referenced in code)"
            else:
                status = "🟡 Active (0 rows, referenced in code)"
        else:
            status = "🔴 Possibly Orphaned (0 rows, 0 code references)"
            
        report_data.append({
            "table": table,
            "rows": row_count,
            "refs": code_refs,
            "seq_scan": t_stats["seq_scan"],
            "idx_scan": t_stats["idx_scan"],
            "inserts": t_stats["inserts"],
            "updates": t_stats["updates"],
            "status": status
        })
        
    cur.close()
    conn.close()
    
    # Generate Markdown Report (Write to /app/scripts so it syncs to host)
    report_path = os.path.join(WORKSPACE_DIR, "scripts", "empty_tables_audit_report.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    from datetime import datetime
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("# Supabase 資料表審計與使用率分析報告\n\n")
        rf.write(f"- **審計時間**: {current_time_str}\n")
        rf.write("- **資料來源**: pg_stat_user_tables & 靜態代碼掃描\n\n")
        
        rf.write("## 1. 所有資料表使用情況總覽\n\n")
        rf.write("| 資料表名稱 | 資料列數量 | 程式碼引用次數 | 循序掃描 (Seq Scan) | 索引掃描 (Idx Scan) | 寫入次數 (Inserts) | 狀態與建議 |\n")
        rf.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        
        orphaned_tables = []
        for r in report_data:
            rf.write(f"| `{r['table']}` | {r['rows']} | {r['refs']} | {r['seq_scan']} | {r['idx_scan']} | {r['inserts']} | {r['status']} |\n")
            if "Possibly Orphaned" in r["status"]:
                orphaned_tables.append(r["table"])
                
        rf.write("\n## 2. 建議清理的孤立資料表 (Possibly Orphaned)\n\n")
        if orphaned_tables:
            rf.write("> [!WARNING]\n")
            rf.write("> 以下資料表目前資料列為 0，且在後端 Python、前端 Admin UI 與 End-User UI 的代碼中皆無發現任何引用字串。建議可安全清理：\n\n")
            for ot in orphaned_tables:
                rf.write(f"- `{ot}`\n")
        else:
            rf.write("✅ 未發現任何無程式碼引用且無資料的孤立資料表。\n")
            
    print(f"🎉 Audit complete! Report generated at: {report_path}")
    print("\nOrphaned tables found:")
    for ot in orphaned_tables:
        print(f" - {ot}")

if __name__ == "__main__":
    run_audit()
