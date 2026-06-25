import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("SUPABASE_DB_SESSION_URL") or os.getenv("SUPABASE_DB_URL")
if not db_url:
    print("❌ No DB URL found in environment.")
    exit(1)

try:
    with open("migration/0.2.2/26_rag_hybrid_match_chunks.sql", "r") as f:
        sql = f.read()

    print("Executing SQL migration...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(sql)
    print("✅ RPC migration applied successfully!")
except Exception as e:
    print(f"❌ Error applying migration: {e}")
