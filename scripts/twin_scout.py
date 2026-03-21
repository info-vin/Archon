import asyncio
import os
import base64
import argparse
import shutil
from datetime import datetime
from supabase import create_client, Client
from playwright.async_api import async_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def parse_args():
    parser = argparse.ArgumentParser(description="Digital Twin Scout v29 - Outbound Intelligence")
    parser.add_argument("--headless", type=str, default="true")
    parser.add_argument("--outbound_url", type=str, default="", help="External URL to inspect for design inspiration.")
    return parser.parse_args()

async def inspect_outbound(pg, target_url, persona_name="Outbound Scout"):
    """Goes directly to an external URL without login to gather inspiration."""
    print(f"🌍 [Scout] Outbound Mission -> {target_url}...")
    try:
        await pg.goto(target_url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3) # Wait for animations
        
        txt = await pg.evaluate("() => document.body.innerText.substring(0, 2000)")
        img = base64.b64encode(await pg.screenshot(full_page=True)).decode("utf-8")
        
        print(f"✅ [Scout] Outbound inspection complete.")
        return {"name": f"Outbound ({target_url})", "image": img, "text": txt}
    except Exception as e:
        print(f"❌ [Scout] Outbound inspection FAILED: {e}")
        return None

async def get_mission_from_db(prompt_name="twin_scout_mission"):
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase: Client = create_client(url, key)
        res = supabase.table("archon_prompts").select("prompt").eq("prompt_name", prompt_name).execute()
        return res.data[0]["prompt"] if res.data else "Standard UI Audit Mission."
    except:
        return "Standard Audit Mission."

async def log_agent_xp(message, xp_change=0):
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase: Client = create_client(url, key)
        supabase.table("archon_logs").insert({
            "source": "agent_action",
            "level": "INFO",
            "message": message,
            "details": {"agent_name": "TwinScout", "xp_change": xp_change, "v": "v28"}
        }).execute()
    except:
        pass

async def inspect_persona(pg, email, target_url, wait_selector, persona_name):
    """Logs in and navigates to the target URL, waiting for a specific selector to prove rendering."""
    print(f"🕵️‍♀️ [Scout] Inspecting {persona_name} ({email}) -> {target_url}...")
    
    # Capture browser console logs for hard evidence
    pg.on("console", lambda msg: print(f"🖥️ [Browser {persona_name}] {msg.type}: {msg.text}"))
    
    try:
        url = os.getenv("ENDUSER_UI_URL", "http://enduser-ui:5173")
        
        # 1. Login
        await pg.goto(f"{url}/#/auth", wait_until="domcontentloaded", timeout=30000)
        await pg.wait_for_selector('input[type="email"]', timeout=30000)
        await pg.fill('input[type="email"]', email)
        await pg.fill('input[type="password"]', "qwer45tyuiop")
        await pg.click('button[type="submit"]')
        
        # 2. Evidence-based Wait: Ensure URL actually changes away from auth
        print(f"⏳ Waiting for login routing to complete...")
        try:
            await pg.wait_for_function('window.location.hash !== "#/auth"', timeout=15000)
        except Exception as e:
            print(f"⚠️ [Scout] URL did not leave /auth. Login might have failed silently: {e}")

        # 3. Navigate to specific target
        await pg.goto(f"{url}/#{target_url}", wait_until="domcontentloaded", timeout=30000)
        
        # 4. Wait for specific content to prove it's NOT infinitely loading
        print(f"⏳ Waiting for {persona_name}'s specific UI elements ({wait_selector})...")
        await pg.wait_for_selector(wait_selector, timeout=30000)
        
        # Extra 2 seconds for API data fetching to settle
        await asyncio.sleep(2)

        txt = await pg.evaluate("() => document.body.innerText.substring(0, 1000)")
        img = base64.b64encode(await pg.screenshot(full_page=True)).decode("utf-8")
        
        # 5. Logout for next persona
        try:
            await pg.click('button:has-text("Logout"), button[aria-label="Logout"], .fa-sign-out-alt', timeout=5000)
            await pg.wait_for_selector('input[type="email"]', timeout=10000)
        except Exception as logout_e:
            print(f"⚠️ [Scout] Logout button not found or failed, clearing cookies instead: {logout_e}")
            await pg.context.clear_cookies()
            
        print(f"✅ [Scout] {persona_name} inspection complete.")
        return {"name": persona_name, "image": img, "text": txt}
    except Exception as e:
        print(f"❌ [Scout] {persona_name} inspection FAILED: {e}")
        try:
            err_img_bytes = await pg.screenshot(full_page=True)
            err_img = base64.b64encode(err_img_bytes).decode("utf-8")
            
            # Save raw PNG for debug
            debug_dir = "./.twin/diagnostics"
            os.makedirs(debug_dir, exist_ok=True)
            safe_name = persona_name.split()[0].lower()
            with open(f"{debug_dir}/error_{safe_name}.png", "wb") as f:
                f.write(err_img_bytes)
                
            return {"name": f"{persona_name} (FAILED)", "image": err_img, "text": f"Error: {e}"}
        except Exception as snap_e:
            return {"name": f"{persona_name} (CRASH)", "text": f"Fatal error: {e}. Screenshot failed: {snap_e}"}

async def run_scout_session():
    args = parse_args()
    is_headless = args.headless.lower() == "true"
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    all_results = []
    
    # 4 Personas Matrix defined in Phase 4.6.8 & 4.6.9
    personas = [
        # Alice (Sales): Check Dashboard for Tasks
        {"email": "alice@archon.com", "url": "/dashboard", "selector": "table, .grid-cols-1", "name": "Alice (Sales)"},
        
        # Bob (Marketing): Check Blog
        {"email": "bob@archon.com", "url": "/marketing", "selector": ".grid-cols-1.md\\:grid-cols-2", "name": "Bob (Marketing)"},
        
        # Charlie (Manager): Check Nexus Data Matrix
        {"email": "charlie@archon.com", "url": "/nexus", "selector": ".recharts-responsive-container", "name": "Charlie (Manager Nexus)"},
        
        # David (Admin): Check System Health on 5173 /admin
        {"email": "admin@archon.com", "url": "/admin", "selector": "text=System Health", "name": "David (Admin Controls)"}
    ]

    async with async_playwright() as p:
        audit_dir = os.path.abspath("./.browser_data/temp_audit")
        if os.path.exists(audit_dir): shutil.rmtree(audit_dir, ignore_errors=True)
        os.makedirs(audit_dir, exist_ok=True)
        
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=audit_dir, 
            headless=is_headless, 
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        pg = await ctx.new_page()
        
        # New: Outbound Scouting (Phase 4.6.15)
        if args.outbound_url:
            outbound_res = await inspect_outbound(pg, args.outbound_url)
            if outbound_res:
                all_results.append(outbound_res)
        
        for p_config in personas:
            res = await inspect_persona(pg, p_config["email"], p_config["url"], p_config["selector"], p_config["name"])
            if res:
                all_results.append(res)
                
        await ctx.close()

    if all_results:
        print("🚀 [Scout] Invoking Gemini Vision for final diagnosis...")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)
        mission_desc = await get_mission_from_db("twin_scout_mission")
        
        system_prompt = (
            f"你是一位強悍的 UX/UI 診斷工程師 Digital Twin Scout。\n"
            f"任務目標：{mission_desc}\n"
            f"請誠實、客觀地根據截圖與文字診斷：\n"
            f"這 4 位角色的 UI 是否成功載入？有沒有無限 Loading 或是連線拒絕的錯誤？"
            f"**注意：請務必全程使用「繁體中文」撰寫此報告。**"
        )
        msg_parts = [{"type": "text", "text": system_prompt}]
        for r in all_results:
            info = f"\n--- Screenshot: {r['name']} ---"
            if "text" in r: info += f"\n[Text Excerpt]: {r['text']}"
            msg_parts.append({"type": "text", "text": info})
            if "image" in r:
                msg_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{r['image']}"}})
            
        try:
            response = await llm.ainvoke([HumanMessage(content=msg_parts)])
            content = response.content
        except Exception as e:
            content = f"Failed to invoke Gemini API: {e}"
        
        report_dir = "./.twin/diagnostics"
        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"{report_dir}/report_{timestamp}.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Twin Scout Agent Report (Multi-Persona)\n- **Time**: {datetime.now().isoformat()}\n\n")
            f.write(content)
            f.write("\n\n---\n**Diagnostician:** Digital Twin Scout v28")
            
        print(f"📄 [Scout] Report saved to: {report_path}")
        await log_agent_xp("Multi-Persona session finished.")

if __name__ == "__main__":
    asyncio.run(run_scout_session())

