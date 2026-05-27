import asyncio

from dotenv import load_dotenv

from src.server.utils import get_supabase_client

load_dotenv(".env")

async def seed_tts_prompts():
    supabase = get_supabase_client()

    prompts = [
        {
            "prompt_name": "tts_marketing_pitch",
            "prompt": "[Voice style: Puck]\n[enthusiastic and convincing] {text}",
            "description": "Template for Bob's marketing pitch audio preview.",
            "is_system_protected": False
        },
        {
            "prompt_name": "tts_commander_briefing",
            "prompt": "[Voice style: Charon]\n[calm and authoritative] 各位早安，我是 Archon。今天的專案「天氣」有些波動。{text} [laughs] 別擔心，Alice 的開發進度依然如陽光般耀眼。",
            "description": "Template for Charlie's daily Manager Nexus briefing.",
            "is_system_protected": False
        }
    ]

    for p in prompts:
        # Check if exists
        res = supabase.table("archon_prompts").select("*").eq("prompt_name", p["prompt_name"]).execute()
        if res.data:
            print(f"Prompt {p['prompt_name']} already exists. Updating...")
            supabase.table("archon_prompts").update(p).eq("prompt_name", p["prompt_name"]).execute()
        else:
            print(f"Inserting prompt {p['prompt_name']}...")
            supabase.table("archon_prompts").insert(p).execute()

if __name__ == "__main__":
    asyncio.run(seed_tts_prompts())
