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
    print("🚀 Fueling 90-Day Task History for Nexus Synergy Matrix...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # 1. Cleanup
    cur.execute("DELETE FROM archon_tasks WHERE title LIKE 'FUELED:%'")

    # 2. Get Project
    cur.execute("SELECT id FROM archon_projects LIMIT 1")
    project_id = cur.fetchone()[0]

    # 3. Get Real Profiles
    cur.execute("SELECT id, name, role FROM profiles")
    all_profiles = cur.fetchall()
    
    # Map for easy simulation
    humans = [p[0] for p in all_profiles if p[2] != 'ai_agent']
    agents = [p[0] for p in all_profiles if p[2] == 'ai_agent']
    all_entities = [p[0] for p in all_profiles]

    if not humans or not agents:
        print("❌ Error: Missing humans or agents in profiles table. Run make db-init first.")
        return

    now = datetime.now(timezone.utc)
    task_count = 0

    # Inject 180 days
    for day in range(180):
        daily_count = random.randint(4, 10)
        target_date = now - timedelta(days=day)
        
        for i in range(daily_count):
            # Create a realistic due date
            # 90% chance of being on time, 10% chance of being late
            is_late = random.random() < 0.1
            
            created_at = (target_date - timedelta(hours=random.randint(24, 48))).isoformat()
            completed_at = target_date.isoformat()
            
            if is_late:
                # Due date is BEFORE completion
                due_date = (target_date - timedelta(hours=random.randint(1, 12))).isoformat()
            else:
                # Due date is AFTER completion
                due_date = (target_date + timedelta(hours=random.randint(1, 24))).isoformat()
            
            # Pick creator and assignee
            creator = random.choice(all_entities)
            assignee = random.choice(humans)
            
            if creator != assignee:
                sources = [{"type": "handoff", "source_id": creator, "title": f"Synergy from {creator}"}]
                
                cur.execute("""
                    INSERT INTO archon_tasks (title, description, project_id, status, assignee_id, assignee, priority, created_at, completed_at, due_date, sources)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f"FUELED: Synergy {day}-{i}",
                    f"Task initiated by {creator}",
                    project_id,
                    "done",
                    assignee,
                    "Automated Worker",
                    "medium",
                    created_at,
                    completed_at,
                    due_date,
                    json.dumps(sources)
                ))
                task_count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Successfully injected {task_count} synergy-rich tasks.")

if __name__ == "__main__":
    fuel_tasks()
