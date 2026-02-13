import os
import random
from datetime import datetime, timedelta, timezone
import psycopg2

# Configuration
DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    print("❌ Error: SUPABASE_DB_URL not found in environment.")
    exit(1)

def fuel_tasks():
    print("🚀 Fueling 90-Day Task History for Nexus Baseline...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # 1. Clear existing generated fuel (optional, but keep it clean)
    cur.execute("DELETE FROM archon_tasks WHERE title LIKE 'FUELED:%'")

    # 2. Identify a project to attach to
    cur.execute("SELECT id FROM archon_projects LIMIT 1")
    project_id = cur.fetchone()[0]

    # 3. Identify a human to assign to
    cur.execute("SELECT id FROM profiles WHERE role = 'sales' LIMIT 1")
    alice_id = cur.fetchone()[0]

    now = datetime.now(timezone.utc)
    task_count = 0

    # Inject 90 days of data
    for day in range(90):
        # Generate 3-8 tasks per day
        daily_count = random.randint(3, 8)
        target_date = now - timedelta(days=day)
        
        for i in range(daily_count):
            task_id = f"fuel-{day}-{i}"
            created_at = (target_date - timedelta(hours=random.randint(1, 12))).isoformat()
            completed_at = target_date.isoformat()
            
            cur.execute("""
                INSERT INTO archon_tasks (title, description, project_id, status, assignee_id, assignee, priority, created_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                f"FUELED: Weekly Sync {day}-{i}",
                "Automated historical seed for Nexus trend verification.",
                project_id,
                "done",
                alice_id,
                "Alice",
                "medium",
                created_at,
                completed_at
            ))
            task_count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Successfully injected {task_count} historical tasks across 90 days.")

if __name__ == "__main__":
    fuel_tasks()
