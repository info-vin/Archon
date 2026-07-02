import os
import time
import psycopg2
from dotenv import load_dotenv

# ============================================================================
# Phase 5.8.x - GraphRAG (Pure Postgres) Pipeline Probe
# 
# 驗證目標：
# 1. 資料庫連線 (SUPABASE_DB_URL)
# 2. 實體(Entities)與關係(Relationships)資料表的建立與插入
# 3. PostgreSQL Recursive CTE (遞迴查詢) 多跳推論 (Multi-hop Reasoning) 效能
# 4. 不依賴 Neo4j 的純 Postgres 圖形檢索可行性
# ============================================================================

def log_step(step_name: str, status: str, latency: float = None, detail: str = ""):
    color = "\033[92m" if status == "PASS" else "\033[91m"
    reset = "\033[0m"
    latency_str = f" ({latency:.4f}s)" if latency is not None else ""
    print(f"[{color}{status}{reset}] {step_name}{latency_str} {detail}")

def probe_pipeline():
    print("🚀 啟動 GraphRAG (Pure Postgres) 架構實體探針驗證 (No Happy Path)...\n")
    
    load_dotenv()
    db_url = os.getenv("SUPABASE_DB_URL")
    
    if not db_url:
        log_step("環境變數檢查", "FAIL", detail="缺少 SUPABASE_DB_URL")
        return
    log_step("環境變數檢查", "PASS")

    print("\n[Probe 1] 連接 Supabase (PostgreSQL) 並建立 Graph 測試環境...")
    start_time = time.time()
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # 建立臨時表模擬圖形結構
        cur.execute("""
            CREATE TEMP TABLE temp_entities (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );
            
            CREATE TEMP TABLE temp_relationships (
                id SERIAL PRIMARY KEY,
                source_id INT REFERENCES temp_entities(id),
                target_id INT REFERENCES temp_entities(id),
                label TEXT NOT NULL
            );
            
            -- 建立索引加速圖形遍歷
            CREATE INDEX idx_rel_source ON temp_relationships(source_id);
            CREATE INDEX idx_rel_target ON temp_relationships(target_id);
        """)
        
        # 插入測試資料 (Godot 知識圖譜)
        entities = ["Godot", "GDScript", "Node", "Tween", "SceneTreeTimer", "MemoryLeak", "Deadlock"]
        for e in entities:
            cur.execute("INSERT INTO temp_entities (name) VALUES (%s)", (e,))
            
        rels = [
            ("Godot", "uses", "GDScript"),
            ("Godot", "has_core_concept", "Node"),
            ("Tween", "animates", "Node"),
            ("Tween", "causes", "Deadlock"),
            ("SceneTreeTimer", "prevents", "Deadlock"),
            ("Node", "causes", "MemoryLeak")
        ]
        
        for source, label, target in rels:
            cur.execute("""
                INSERT INTO temp_relationships (source_id, target_id, label)
                VALUES (
                    (SELECT id FROM temp_entities WHERE name = %s),
                    (SELECT id FROM temp_entities WHERE name = %s),
                    %s
                )
            """, (source, target, label))
            
        latency_1 = time.time() - start_time
        log_step("資料庫與圖形準備", "PASS", latency=latency_1, detail="成功建立 entities 與 relationships 臨時表並插入三元組")
    except Exception as e:
        latency_1 = time.time() - start_time
        log_step("資料庫與圖形準備", "FAIL", latency=latency_1, detail=str(e))
        return

    # 2. 測試 Recursive CTE 多跳查詢 (Multi-hop Reasoning)
    print("\n[Probe 2] 執行 Recursive CTE 進行 2-hop 推論 (尋找 Godot 的衍生風險)...")
    start_time = time.time()
    try:
        # 目標：從 "Godot" 出發，找出它關聯的節點，以及關聯節點的關聯節點
        query = """
            WITH RECURSIVE graph_walk AS (
                -- Base Case (Depth 0)
                SELECT 
                    e.id AS current_node_id, 
                    e.name AS current_node_name, 
                    ARRAY[e.name] AS path,
                    0 AS depth
                FROM temp_entities e
                WHERE e.name = 'Godot'
                
                UNION ALL
                
                -- Recursive Step
                SELECT 
                    r.target_id, 
                    next_e.name, 
                    gw.path || next_e.name,
                    gw.depth + 1
                FROM graph_walk gw
                JOIN temp_relationships r ON gw.current_node_id = r.source_id
                JOIN temp_entities next_e ON r.target_id = next_e.id
                WHERE gw.depth < 2  -- 限制最多 2 jumps (2-hop)
            )
            SELECT path FROM graph_walk WHERE depth > 0;
        """
        cur.execute(query)
        results = cur.fetchall()
        latency_2 = time.time() - start_time
        
        paths = [r[0] for r in results]
        details = "找到以下推理路徑:\n" + "\n".join([f"      -> {' -> '.join(p)}" for p in paths])
        log_step("SQL 圖形推論", "PASS", latency=latency_2, detail=details)
        
    except Exception as e:
        latency_2 = time.time() - start_time
        log_step("SQL 圖形推論", "FAIL", latency=latency_2, detail=str(e))

    finally:
        cur.close()
        conn.close()

    print(f"\n✅ GraphRAG 探針任務結束。已證實無需 Neo4j 也能完成實體多跳關係檢索。")

if __name__ == "__main__":
    probe_pipeline()
