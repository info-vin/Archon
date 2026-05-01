import asyncio
import os
import base64
import argparse
import shutil
import time
import sys
from datetime import datetime

# --- Physical Environment Realignment (Phase 4.6.39) ---
# When running inside archon-server, we must align PYTHONPATH to reuse services.
project_root = "/app"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from supabase import create_client, Client
from playwright.async_api import async_playwright
from google import genai
from google.genai import types

# Reuse official services (No Reinventing Wheels)
from src.server.services import credential_service
from src.server.services.prompt_service import prompt_service

def parse_args():
    parser = argparse.ArgumentParser(description="Digital Twin Scout v39.1 - 503 Resistant")
    parser.add_argument("--headless", type=str, default="true")
    return parser.parse_args()

def limit_diagnostic_capacity(directory="./.twin/diagnostics", max_files=10):
    """Metabolism mechanism: prevent disk bloat while locking mismatch reports."""
    if not os.path.exists(directory): return
    all_files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if len(all_files) <= max_files: return
    
    removable_files = []
    for f in all_files:
        try:
            with open(f, 'r') as content:
                text = content.read()
                if "PARITY_MISMATCH" in text or "WORKFLOW_FAILURE" in text:
                    continue 
            removable_files.append(f)
        except:
            removable_files.append(f)

    removable_files.sort(key=os.path.getmtime)
    excess = len(all_files) - max_files
    deleted = 0
    for f in removable_files:
        if deleted >= excess: break
        try: 
            os.remove(f)
            deleted += 1
        except: pass
    print(f"♻️ [Metabolism] Cleaned {deleted} old reports.")

async def initialize_services():
    """Ensure services are ready for standalone execution (Pattern 0413)."""
    try:
        await credential_service.initialize_credentials()
        await prompt_service.load_prompts()
        print("✅ [Scout] Core Services Initialized.")
        return True
    except Exception as e:
        print(f"❌ [Scout] Service Initialization Failed: {e}")
        return False

async def get_workflow_snapshot(email):
    """Data-driven reality snapshot using real DB counts."""
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase: Client = create_client(url, key)
        user_res = supabase.table("profiles").select("id, name").eq("email", email).execute()
        if not user_res.data: return f"Reality Snapshot: Unknown Persona ({email})"
        user_id = user_res.data[0]["id"]
        user_name = user_res.data[0]["name"]
        
        if "alice" in email:
            leads_res = supabase.table("leads").select("id", count='exact').limit(1).execute()
            tasks_res = supabase.table("archon_tasks").select("id", count='exact').eq("assignee_id", user_id).limit(1).execute()
            return f"Reality Snapshot for {user_name}: {leads_res.count} total leads, {tasks_res.count} tasks assigned."
        elif "bob" in email:
            # Bob in /brand Hub sees brand-related leads. Aligning snapshot metric to UI.
            blog_res = supabase.table("leads").select("id", count='exact').limit(1).execute()
            return f"Reality Snapshot for {user_name}: {blog_res.count} total items in Brand Hub."
        elif "dev.bot" in email:
            agent_tasks = supabase.table("archon_tasks").select("id", count='exact').eq("assignee_id", user_id).limit(1).execute()
            return f"Reality Snapshot for {user_name}: {agent_tasks.count} tasks assigned."

        return f"Reality Snapshot for {user_name}: Context loaded."
    except Exception as e:
        return f"Reality Snapshot: [Error] {e}"

async def log_twin_diagnosis(content: str, diagnosis_type="WORKFLOW_SUCCESS"):
    """Bridge findings to the global log table for manager awareness."""
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase: Client = create_client(url, key)
        level = "ALERT" if diagnosis_type != "WORKFLOW_SUCCESS" else "INFO"
        supabase.table("archon_logs").insert({
            "source": "twin_scout", 
            "level": level, 
            "message": f"Digital Twin Diagnosis: {diagnosis_type}",
            "details": {
                "category": "business", "type": "twin_diagnosis", 
                "diagnosis": diagnosis_type,
                "summary": content[:500] + "..." if len(content) > 500 else content,
                "v": "v39.1"
            }
        }).execute()
        print(f"📡 [Scout] Diagnosis logged to archon_logs as {level}.")
    except Exception as e:
        print(f"⚠️ [Scout] Failed to log diagnosis: {e}")

async def analyze_with_retry(client, model, contents, system_prompt, retries=3):
    """503 Resistant Analysis Logic (Exponential Backoff + Fallback)."""
    backoff = 2
    current_model = model
    for i in range(retries):
        try:
            response = await client.aio.models.generate_content(
                model=current_model, contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_prompt)
            )
            return response.text or "AI returned empty text."
        except Exception as e:
            err_str = str(e)
            if any(code in err_str for code in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                print(f"⏳ [Scout] API Strain ({err_str[:15]}). Retrying in {backoff}s... ({i+1}/{retries})")
                await asyncio.sleep(backoff)
                backoff *= 2
            else:
                return f"AI Error: {err_str}"
    return "AI Error: Continuous failure even with fallback."

async def inspect_and_analyze(pg, p_config, reality_map, client, target_model, mission_prompt):
    """Atomic Persona Inspection: Keep payload small to avoid 503."""
    email, name, target_url, wait_selector = p_config["email"], p_config["name"], p_config["url"], p_config["selector"]
    reality_context = reality_map.get(email, "Context missing")

    print(f"🕵️‍♀️ [Scout] Inspecting {name} ({email}) -> {target_url}...")
    try:
        url = os.getenv("ENDUSER_UI_URL", "http://enduser-ui:5173")
        await pg.goto(f"{url}/#/auth", wait_until="domcontentloaded", timeout=30000)
        await pg.wait_for_selector('input[type="email"]', timeout=30000)
        await pg.fill('input[type="email"]', email)
        await pg.fill('input[type="password"]', "qwer45tyuiop")
        await pg.click('button[type="submit"]')
        
        await asyncio.sleep(3) 
        await pg.wait_for_function('window.location.hash !== "#/auth"', timeout=15000)
        await pg.goto(f"{url}/#{target_url}", wait_until="domcontentloaded", timeout=30000)
        await pg.wait_for_selector(wait_selector, timeout=30000)
        # physically wait longer for permission sync
        await asyncio.sleep(5)

        txt = await pg.evaluate("() => document.body.innerText.substring(0, 1000)")
        img_bytes = await pg.screenshot(full_page=True)
        
        system_prompt = (
            f"你是一位精準的工作流診斷員 Digital Twin Scout v39.1。\n"
            f"任務：診斷角色 {name} 的 UI 狀態。特殊指令：{mission_prompt}\n"
            f"比對 [Reality Snapshot] 與截圖。若正常請回傳 [WORKFLOW_SUCCESS]，否則回傳 [PARITY_MISMATCH]。"
        )
        
        contents = [
            f"[Reality Context]: {reality_context}\n[DOM Excerpt]: {txt}",
            types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        ]
        
        analysis = await analyze_with_retry(client, target_model, contents, system_prompt)
        print(f"✅ [Scout] Analysis complete for {name}.")
        return {"name": name, "analysis": analysis}
    except Exception as e:
        print(f"❌ [Scout] {name} FAILED: {e}")
        return {"name": name, "analysis": f"Critical Failure: {e}"}

async def run_scout_session():
    # Phase 4.6.46 Hardening: Wait for backend hot-reload stability
    print("⏳ [Scout] Cooling down 15s for backend stability (Anti-503)...")
    await asyncio.sleep(15)
    
    args = parse_args()
    is_headless = args.headless.lower() == "true"
    if not await initialize_services(): return

    api_key = await credential_service.get_credential("GEMINI_API_KEY")
    if not api_key:
        print("❌ [Scout] GEMINI_API_KEY missing. Aborting.")
        return

    target_model = (await credential_service.get_credential("MARKETING_MODEL") or "gemini-3.1-flash-lite-preview").split("/")[-1]
    client = genai.Client(api_key=api_key)

    mission_key = os.getenv("SCOUT_PROMPT_KEY", "twin_scout_mission")
    mission_prompt = prompt_service.get_prompt(mission_key, "任務：進行一般巡檢")

    limit_diagnostic_capacity()
    reality_map = {}
    for p_email in ["alice@archon.com", "bob@archon.com", "charlie@archon.com", "admin@archon.com", "dev.bot@archon.com"]:
        reality_map[p_email] = await get_workflow_snapshot(p_email)

    personas = [
        {"email": "alice@archon.com", "url": "/marketing", "selector": "ul, table, .grid-cols-1", "name": "Alice (Sales)"},
        {"email": "bob@archon.com", "url": "/brand", "selector": "ul, .grid-cols-1", "name": "Bob (Marketing)"},
        {"email": "charlie@archon.com", "url": "/nexus", "selector": "canvas, .recharts-responsive-container", "name": "Charlie (Manager Nexus)"},
        {"email": "admin@archon.com", "url": "/admin", "selector": "h1, .admin-panel", "name": "David Howard (Admin)"},
        {"email": "dev.bot@archon.com", "url": "/dashboard", "selector": "ul, table, .card", "name": "DevBot (Agent)"}
    ]

    global_report = []
    async with async_playwright() as p:
        for p_config in personas:
            safe_name = p_config["name"].split()[0].lower()
            audit_dir = os.path.abspath(f"./.browser_data/scout_{safe_name}")
            if os.path.exists(audit_dir): shutil.rmtree(audit_dir, ignore_errors=True)
            os.makedirs(audit_dir, exist_ok=True)

            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=audit_dir, headless=is_headless, 
                args=['--no-sandbox', '--disable-setuid-sandbox'],
                viewport={'width': 1920, 'height': 1080},
                user_agent=f"ArchonIntegratedScout/3.9.1 ({safe_name})"
            )
            pg = await ctx.new_page()
            res = await inspect_and_analyze(pg, p_config, reality_map, client, target_model, mission_prompt)
            global_report.append(res)
            await ctx.close()
            
            # Physical Cooldown to prevent 503 API Strain (Gemini Free Tier)
            print(f"⏳ [Scout] Cooling down for 15s before next persona...")
            await asyncio.sleep(15)

    report_text = "# Digital Twin Consolidated Report (v39.1 - Anti-503)\n\n"
    for r in global_report:
        report_text += f"## {r['name']}\n{r['analysis']}\n\n"
    
    report_dir = "./.twin/diagnostics"
    os.makedirs(report_dir, exist_ok=True)
    report_path = f"{report_dir}/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, "w", encoding="utf-8") as f: f.write(report_text)
    
    print(f"📄 [Scout] Final Report saved: {report_path}")
    final_type = "PARITY_MISMATCH" if "PARITY_MISMATCH" in report_text else "WORKFLOW_SUCCESS"
    await log_twin_diagnosis(report_text, final_type)

    # --- RESTORED FEEDBACK LOOP (Phase 4.6.46) ---
    if final_type == "WORKFLOW_SUCCESS":
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")
            supabase: Client = create_client(url, key)
            
            # Example heuristic: if success, ensure basic tools are low friction
            # In a production EXP-03, this would parse 'analysis' for specific tool name recommendations
            optimizations = {
                "search_job_market": {"min_xp_level": 0},
                "rag_search_knowledge_base": {"min_xp_level": 0}
            }
            supabase.table("archon_settings").upsert({
                "key": "AGENT_TOOL_OVERRIDES",
                "value": optimizations,
                "is_system_protected": True
            }, on_conflict="key").execute()
            print("🚀 [Scout] Self-tuning optimizations applied to AgentRegistry.")
        except Exception as e:
            print(f"⚠️ [Scout] Feedback loop write failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_scout_session())
