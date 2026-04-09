import asyncio
import os
import base64
import argparse
import shutil
import time
import requests
from datetime import datetime
from supabase import create_client, Client
from playwright.async_api import async_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def parse_args():
    parser = argparse.ArgumentParser(description="Digital Twin Scout v36 - Isolated Perception")
    parser.add_argument("--headless", type=str, default="true")
    parser.add_argument("--outbound_url", type=str, default="", help="External URL to inspect.")
    return parser.parse_args()

def limit_diagnostic_capacity(directory="./.twin/diagnostics", max_files=10):
    if not os.path.exists(directory): return
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if len(files) <= max_files: return
    normal_files = sorted([os.path.join(directory, f) for f in os.listdir(directory)], key=os.path.getmtime)
    excess = len(normal_files) - max_files
    for i in range(excess):
        try: os.remove(normal_files[i])
        except: pass

async def get_workflow_snapshot(email):
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase: Client = create_client(url, key)
        user_res = supabase.table("profiles").select("id, name").eq("email", email).execute()
        if not user_res.data: return f"Reality Snapshot: Unknown Persona ({email})"
        user_id = user_res.data[0]["id"]
        user_name = user_res.data[0]["name"]
        
        if "alice" in email:
            leads_res = supabase.table("leads").select("id").execute()
            tasks_res = supabase.table("archon_tasks").select("id").eq("assignee_id", user_id).execute()
            return f"Reality Snapshot for {user_name}: {len(leads_res.data)} total leads, {len(tasks_res.data)} tasks assigned."
        elif "bob" in email:
            blog_res = supabase.table("blog_posts").select("id").execute()
            return f"Reality Snapshot for {user_name}: {len(blog_res.data)} total posts."
        elif "dev.bot" in email:
            agent_tasks = supabase.table("archon_tasks").select("id").eq("assignee_id", user_id).execute()
            return f"Reality Snapshot for {user_name}: {len(agent_tasks.data)} tasks assigned."

        return f"Reality Snapshot for {user_name}: Context loaded."
    except Exception as e:
        return f"Reality Snapshot: [Error] {e}"

async def wait_for_server_ready(url, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            resp = requests.get(f"{url}/api/health", timeout=5)
            if resp.status_code == 200: return True
        except: pass
        await asyncio.sleep(3)
    return False

async def log_agent_xp(message, xp_change=0):
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase: Client = create_client(url, key)
        supabase.table("archon_logs").insert({
            "source": "agent_action", "level": "INFO", "message": message,
            "details": {"agent_name": "TwinScout", "xp_change": xp_change, "v": "v36"}
        }).execute()
    except: pass

async def inspect_persona(pg, email, target_url, wait_selector, persona_name):
    print(f"🕵️‍♀️ [Scout] Inspecting {persona_name} ({email}) -> {target_url}...")
    
    # physical log capture for audit
    pg.on("console", lambda msg: print(f"🖥️ [Browser {persona_name}] {msg.type.upper()}: {msg.text}"))
    pg.on("pageerror", lambda err: print(f"🚨 [Browser FATAL {persona_name}]: {err.message}"))
    
    reality_context = await get_workflow_snapshot(email)

    try:
        url = os.getenv("ENDUSER_UI_URL", "http://enduser-ui:5173")
        await pg.goto(f"{url}/#/auth", wait_until="domcontentloaded", timeout=30000)
        await pg.wait_for_selector('input[type="email"]', timeout=30000)
        await pg.fill('input[type="email"]', email)
        await pg.fill('input[type="password"]', "qwer45tyuiop")
        await pg.click('button[type="submit"]')
        
        # --- Physical Parity: Wait for Session Initialization ---
        await asyncio.sleep(3) 
        
        await pg.wait_for_function('window.location.hash !== "#/auth"', timeout=15000)
        await pg.goto(f"{url}/#{target_url}", wait_until="domcontentloaded", timeout=30000)
        await pg.wait_for_selector(wait_selector, timeout=30000)
        await asyncio.sleep(2)

        txt = await pg.evaluate("() => document.body.innerText.substring(0, 1000)")
        img = base64.b64encode(await pg.screenshot(full_page=True)).decode("utf-8")
        
        return {"name": persona_name, "image": img, "text": txt, "reality": reality_context}
    except Exception as e:
        print(f"❌ [Scout] {persona_name} FAILED: {e}")
        try:
            err_img = base64.b64encode(await pg.screenshot(full_page=True)).decode("utf-8")
            return {"name": f"{persona_name} (FAILED)", "image": err_img, "text": f"Error: {e}", "reality": reality_context}
        except:
            return {"name": f"{persona_name} (CRASH)", "text": f"Fatal error: {e}", "reality": reality_context}

async def run_scout_session():
    args = parse_args()
    is_headless = args.headless.lower() == "true"
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    all_results = []

    limit_diagnostic_capacity()
    server_url = os.getenv("ARCHON_SERVER_URL", "http://archon-server:8181")
    await wait_for_server_ready(server_url)
    
    personas = [
        {"email": "alice@archon.com", "url": "/dashboard", "selector": "ul, table, .grid-cols-1", "name": "Alice (Sales)"},
        {"email": "bob@archon.com", "url": "/marketing", "selector": "ul, .grid-cols-1", "name": "Bob (Marketing)"},
        {"email": "charlie@archon.com", "url": "/nexus", "selector": "canvas, .recharts-responsive-container", "name": "Charlie (Manager Nexus)"},
        {"email": "admin@archon.com", "url": "/admin", "selector": "h1, .admin-panel", "name": "David Howard (Admin)"},
        {"email": "dev.bot@archon.com", "url": "/dashboard", "selector": "ul, table, .card", "name": "DevBot (Agent)"}
    ]

    async with async_playwright() as p:
        for p_config in personas:
            # --- CRITICAL PARITY FIX: Physical Context Isolation ---
            safe_name = p_config["name"].split()[0].lower()
            audit_dir = os.path.abspath(f"./.browser_data/scout_{safe_name}")
            if os.path.exists(audit_dir): shutil.rmtree(audit_dir, ignore_errors=True)
            os.makedirs(audit_dir, exist_ok=True)
            
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=audit_dir, headless=is_headless, 
                args=['--no-sandbox', '--disable-setuid-sandbox'],
                viewport={'width': 1920, 'height': 1080},
                user_agent=f"ArchonIsolatedScout/3.6 ({safe_name})"
            )
            pg = await ctx.new_page()
            res = await inspect_persona(pg, p_config["email"], p_config["url"], p_config["selector"], p_config["name"])
            if res: all_results.append(res)
            await ctx.close()

    if all_results:
        print("🚀 [Scout] Invoking Gemini Vision for isolated workflow alignment...")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)
        
        system_prompt = (
            f"你是一位強悍的工作流診斷工程師 Digital Twin Scout v36。\n"
            f"任務：比對 [Reality Snapshot] (來自 DB) 與截圖是否一致。\n"
            f"若發現 403 或 Permission Denied，請標註為 **[RBAC_FAILURE]**。\n"
            f"若數據不對齊，請標註為 **[PARITY_MISMATCH]**。\n"
            f"全程使用「繁體中文」撰寫此報告。"
        )
        msg_parts = [{"type": "text", "text": system_prompt}]
        for r in all_results:
            info = f"\n--- Persona: {r['name']} ---\n[Reality Context]: {r['reality']}"
            if "text" in r: info += f"\n[Text Excerpt]: {r['text']}"
            msg_parts.append({"type": "text", "text": info})
            if "image" in r:
                msg_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{r['image']}"}})
            
        try:
            response = await llm.ainvoke([HumanMessage(content=msg_parts)])
            content = response.content
        except Exception as e: content = f"Failed to invoke Gemini API: {e}"
        
        report_dir = "./.twin/diagnostics"
        os.makedirs(report_dir, exist_ok=True)
        report_path = f"{report_dir}/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Twin Scout Isolated Report (v36)\n- **Generated**: {datetime.now().isoformat()}\n\n")
            f.write(content)
            f.write("\n\n---\n**Diagnostician:** Digital Twin Scout v36 (Isolated)")
        print(f"📄 [Scout] Report saved: {report_path}")

if __name__ == "__main__":
    asyncio.run(run_scout_session())
