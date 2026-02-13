import os
import random
import json
from datetime import datetime, timedelta, timezone
import psycopg2

# Configuration
DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    print("❌ Error: SUPABASE_DB_URL not found in environment.")
    exit(1)

def fuel_tasks():
    print("🚀 Fueling Nexus All-Force History (Synergy, Act Force, ROI)...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # 1. Cleanup
    cur.execute("DELETE FROM archon_tasks WHERE title LIKE 'FUELED:%'")
    cur.execute("DELETE FROM archon_sources WHERE source_id LIKE 'fuel-crawl-%'")

    # 2. Setup Nodes
    cur.execute("SELECT id, name, role FROM profiles")
    all_profiles = cur.fetchall()
    humans = [p[0] for p in all_profiles if p[2] != 'ai_agent']
    agents = [p[0] for p in all_profiles if p[2] == 'ai_agent']
    all_entities = [p[0] for p in all_profiles]
    
    cur.execute("SELECT id FROM archon_projects LIMIT 1")
    project_id = cur.fetchone()[0]

    now = datetime.now(timezone.utc)

    # --- FUEL TASK SYNERGY (180 Days) ---
    for day in range(180):
        target_date = now - timedelta(days=day)
        for i in range(random.randint(4, 8)):
            is_late = random.random() < 0.1
            created_at = (target_date - timedelta(hours=random.randint(24, 48))).isoformat()
            completed_at = target_date.isoformat()
            due_date = (target_date - timedelta(hours=random.randint(1, 12))).isoformat() if is_late else (target_date + timedelta(hours=random.randint(1, 24))).isoformat()
            
            creator = random.choice(all_entities)
            assignee = random.choice(humans)
            if creator != assignee:
                sources = [{"type": "handoff", "source_id": creator, "title": f"Synergy from {creator}"}]
                cur.execute("""
                    INSERT INTO archon_tasks (title, description, project_id, status, assignee_id, assignee, priority, created_at, completed_at, due_date, sources)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (f"FUELED: Synergy {day}-{i}", f"Task by {creator}", project_id, "done", assignee, "Team Member", "medium", created_at, completed_at, due_date, json.dumps(sources)))

    # --- FUEL KNOWLEDGE ROI (60 Days) ---
    domains = [
        {"url": "https://sas.com/ai", "quality": 0.95},
        {"url": "https://github.com/archon", "quality": 0.8},
        {"url": "https://microsoft.com/docs", "quality": 0.6},
        {"url": "https://linkedin.com/noise", "quality": 0.1}
    ]

    for day in range(60):
        target_date = now - timedelta(days=day)
        for dom_cfg in domains:
            scanned = random.randint(5, 12)
            for i in range(scanned):
                sid = f"fuel-crawl-{day}-{dom_cfg['url'].split('/')[-1]}-{i}"
                cur.execute("""
                    INSERT INTO archon_sources (source_id, source_url, created_at, title)
                    VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
                """, (sid, dom_cfg['url'], target_date.isoformat(), f"Source {i}"))
                
                if random.random() < dom_cfg['quality']:
                    cur.execute("""
                        INSERT INTO archon_crawled_pages (source_id, created_at, content, url, title, chunk_number, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
                    """, (sid, target_date.isoformat(), "High value content", f"{dom_cfg['url']}/p{i}", f"Page {i}", 1, json.dumps({})))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ All-Force Data Fueling Complete.")

if __name__ == "__main__":
    fuel_tasks()
