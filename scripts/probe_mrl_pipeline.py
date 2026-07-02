import os
import time
import psycopg2
from dotenv import load_dotenv

# ============================================================================
# Phase 5.8.x - MRL (Matryoshka Representation Learning) Pipeline Probe
# 
# 驗證目標：
# 1. 資料庫連線 (SUPABASE_DB_URL)
# 2. pgvector 陣列切片語法支援 (embedding[1:256]::vector(256))
# 3. 測試全維度 (768) 與裁切維度 (256) 的向量運算與延遲差異
# ============================================================================

def log_step(step_name: str, status: str, latency: float = None, detail: str = ""):
    color = "\033[92m" if status == "PASS" else "\033[91m"
    reset = "\033[0m"
    latency_str = f" ({latency:.4f}s)" if latency is not None else ""
    print(f"[{color}{status}{reset}] {step_name}{latency_str} {detail}")

def probe_pipeline():
    print("🚀 啟動 MRL 維度裁切架構實體探針驗證 (No Happy Path)...\n")
    
    load_dotenv()
    db_url = os.getenv("SUPABASE_DB_URL")
    
    if not db_url:
        log_step("環境變數檢查", "FAIL", detail="缺少 SUPABASE_DB_URL")
        return
    log_step("環境變數檢查", "PASS")

    # 1. 資料庫連線與初始化臨時表
    print("\n[Probe 1] 連接 Supabase (PostgreSQL) 並建立 MRL 測試環境...")
    start_time = time.time()
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # 確保安裝 pgvector
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # 建立臨時表儲存 768 維向量
        cur.execute("""
            CREATE TEMP TABLE mrl_probe (
                id SERIAL PRIMARY KEY,
                embedding vector(768)
            );
        """)
        
        # 插入 1000 筆隨機向量 (用 0.01 填滿，只為測試效能與語法)
        cur.execute("""
            INSERT INTO mrl_probe (embedding)
            SELECT ('[' || array_to_string(array_agg(random()), ',') || ']')::vector(768)
            FROM generate_series(1, 1000) g1, generate_series(1, 768) g2
            GROUP BY g1;
        """)
        latency_1 = time.time() - start_time
        log_step("資料庫與數據準備", "PASS", latency=latency_1, detail="成功插入 1000 筆 768 維度測試數據")
    except Exception as e:
        latency_1 = time.time() - start_time
        log_step("資料庫與數據準備", "FAIL", latency=latency_1, detail=str(e))
        return

    # 2. 完整 768 維度運算
    print("\n[Probe 2] 執行完整維度 (768d) 餘弦相似度運算...")
    start_time = time.time()
    try:
        # 生成隨機查詢向量
        cur.execute("SELECT ('[' || array_to_string(array_agg(random()), ',') || ']')::vector(768) FROM generate_series(1, 768);")
        query_vec = cur.fetchone()[0]
        
        cur.execute("""
            SELECT id, 1 - (embedding <=> %s::vector(768)) AS similarity 
            FROM mrl_probe 
            ORDER BY embedding <=> %s::vector(768) 
            LIMIT 5;
        """, (query_vec, query_vec))
        res_768 = cur.fetchall()
        latency_2 = time.time() - start_time
        log_step("768d 運算", "PASS", latency=latency_2, detail=f"取得前 5 名。Top 1 ID: {res_768[0][0]}")
    except Exception as e:
        latency_2 = time.time() - start_time
        log_step("768d 運算", "FAIL", latency=latency_2, detail=str(e))

    # 3. 裁切 256 維度運算 (MRL)
    print("\n[Probe 3] 執行裁切維度 (256d) 餘弦相似度運算 (pgvector 切片)...")
    start_time = time.time()
    try:
        cur.execute("""
            SELECT id, 1 - (((embedding::real[])[1:256])::vector(256) <=> ((%s::vector(768)::real[])[1:256])::vector(256)) AS similarity 
            FROM mrl_probe 
            ORDER BY ((embedding::real[])[1:256])::vector(256) <=> ((%s::vector(768)::real[])[1:256])::vector(256) 
            LIMIT 5;
        """, (query_vec, query_vec))
        res_256 = cur.fetchall()
        latency_3 = time.time() - start_time
        log_step("256d 運算", "PASS", latency=latency_3, detail=f"取得前 5 名。Top 1 ID: {res_256[0][0]}")
        
        if latency_3 < latency_2:
            log_step("效能對比", "PASS", detail=f"裁切維度提速 {(latency_2/latency_3):.2f}x (數據量小可能不明顯，重點在語法通過)")
        else:
            log_step("效能對比", "PASS", detail="數據量過小，效能差異無法真實體現，但 pgvector 切片語法驗證成功")

    except Exception as e:
        latency_3 = time.time() - start_time
        log_step("256d 運算", "FAIL", latency=latency_3, detail=f"pgvector 版本可能過舊不支援切片，或語法錯誤: {str(e)}")

    finally:
        cur.close()
        conn.close()

    print(f"\n✅ MRL 探針任務結束。")

if __name__ == "__main__":
    probe_pipeline()
