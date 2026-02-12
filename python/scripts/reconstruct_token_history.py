import asyncio
import datetime
import random
import uuid

from src.server.utils import get_supabase_client


async def fuel_tokens():
    print("🚀 Reconstructing 30-day Token Usage History...")
    supabase = get_supabase_client()

    # 1. 獲取真實 Profile
    res_profiles = supabase.table("profiles").select("id, name, role").execute()
    profiles = res_profiles.data or []

    if not profiles:
        print("❌ No profiles found. Aborting.")
        return

    all_actors = profiles + [{"id": None, "name": "System (Bot)", "role": "system"}]

    tasks = {
        "marketing": [("104_search", "Crawler/Research"), ("blog_gen", "LLM/Generation")],
        "sales": [("lead_enrich", "Crawler/Research"), ("pitch_gen", "LLM/Generation")],
        "manager": [("strategy_scan", "Crawler/Research")],
        "admin": [("system_probe", "Crawler/Research")],
        "system": [("sentinel_scan", "Crawler/Research")]
    }

    today = datetime.datetime.now(datetime.UTC)
    all_entries = []

    for i in range(30, -1, -1):
        target_date = today - datetime.timedelta(days=i)
        is_weekend = target_date.weekday() >= 5

        for actor in all_actors:
            role = actor['role'].lower()
            u_id = actor['id']
            num_tasks = random.randint(0, 1) if is_weekend else random.randint(3, 8)

            for _ in range(num_tasks):
                task_info = random.choice(tasks.get(role, [("general", "LLM/Generation")]))
                category = task_info[1]

                total = random.randint(8000, 60000)
                i_tokens = int(total * 0.7)
                o_tokens = total - i_tokens
                cost = (total / 1000000) * 2.0
                ts = target_date.replace(hour=random.randint(9, 19), minute=random.randint(0, 59), second=0).isoformat()

                all_entries.append({
                    "request_id": f"sim-{uuid.uuid4().hex[:8]}",
                    "user_id": u_id,
                    "model": "gemini-2.5-flash",
                    "provider": "google",
                    "input_tokens": i_tokens,
                    "output_tokens": o_tokens,
                    "cost_usd": round(cost, 5),
                    "context_type": category,
                    "created_at": ts
                })

    print(f"🧹 Cleaning and Injecting {len(all_entries)} records...")
    supabase.table("token_usage").delete().neq("model", "DELETED").execute()

    batch_size = 100
    for j in range(0, len(all_entries), batch_size):
        supabase.table("token_usage").insert(all_entries[j:j+batch_size]).execute()

    print(f"✅ Real-logic History Restored. Cost: ${sum(e['cost_usd'] for e in all_entries):.2f}")

if __name__ == "__main__":
    asyncio.run(fuel_tokens())
