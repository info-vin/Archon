import os
import psycopg2

DB_URL = os.getenv("SUPABASE_DB_URL")

def fix_digit_avatars():
    print("🛠 Repairing task assignee names (Fixing digit avatars)...")
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # SQL to update assignee name from profiles table where assignee is currently a UUID
        sql = """
        UPDATE archon_tasks t
        SET assignee = p.name
        FROM profiles p
        WHERE t.assignee_id = p.id
        AND t.assignee ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}';
        """
        
        cursor.execute(sql)
        print(f"✅ Repaired {cursor.rowcount} tasks.")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Repair failed: {e}")

if __name__ == "__main__":
    fix_digit_avatars()
