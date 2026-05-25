import asyncio
import os
import base64
import argparse
import shutil
import time
import sys
from datetime import datetime
from dotenv import load_dotenv
# Load environment variables from host .env or python/.env
for p in [".env", "python/.env", "../.env", "../python/.env"]:
    if os.path.exists(p):
        load_dotenv(p)

# --- Physical Environment Realignment (Phase 4.6.39 / 5.1.7) ---
# Align PYTHONPATH dynamically for both Docker (/app) and Host (local workspace)
for p in ["/app", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python"))]:
    if p not in sys.path:
        sys.path.insert(0, p)

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
    parser.add_argument("--mode", type=str, default="audit", choices=["audit", "action", "fanout"])
    parser.add_argument("--record", type=str, default="false", choices=["true", "false"])
    parser.add_argument("--scenario", type=str, default="", help="Path to YAML scenario file")
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
        
        # Save screenshot locally for debugging
        os.makedirs("./.twin/diagnostics", exist_ok=True)
        with open(f"./.twin/diagnostics/{name.split()[0]}.png", "wb") as f:
            f.write(img_bytes)
        
        system_prompt = (
            f"你是一位精準的工作流診斷員 Digital Twin Scout v39.1。\n"
            f"任務：診斷角色 {name} 的 UI 狀態。特殊指令：{mission_prompt}\n"
            f"比對 [Reality Snapshot] 與截圖。若正常請回傳 [WORKFLOW_SUCCESS]，否則回傳 [PARITY_MISMATCH]。\n"
            f"重要規定：請務必全程使用繁體中文（zh-TW）撰寫報告，絕對不可使用簡體中文。\n"
            f"注意：若 Reality Snapshot 顯示 0 tasks assigned，UI 左側導覽列的「My Tasks」項目旁預設不會顯示任何數字標記，此為正常現象，請勿將其視為異常。"
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

import yaml
import importlib

class YAMLScenarioRunner:
    def __init__(self, yaml_path, client, target_model, is_record, headless):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.client = client
        self.target_model = target_model
        self.is_record = is_record
        self.headless = headless
        
    async def run(self):
        print(f"🚀 [Scout-Runner] Executing scenario: {self.config.get('name', 'Unknown')}")
        
        # Pre-hooks
        hooks = self.config.get("hooks", {})
        if "before_auth" in hooks:
            for hook in hooks["before_auth"]:
                if hook["type"] == "python_function":
                    mod = importlib.import_module(hook["module"])
                    func = getattr(mod, hook["function"])
                    print(f"⏳ [Scout-Runner] Running pre-hook: {hook['module']}.{hook['function']}")
                    if asyncio.iscoroutinefunction(func):
                        await func()
                    else:
                        func()

        url = os.getenv("ENDUSER_UI_URL", "http://localhost:5173")
        from cookie_injector import KeychainBypassCookieInjector
        
        async with async_playwright() as p:
            record_dir = "./.twin/videos/temp" if self.is_record else None
            record_size = self.config.get("resolution", {"width": 1280, "height": 720}) if self.is_record else None
            
            browser, ctx = await KeychainBypassCookieInjector.create_keychain_bypass_context(
                p, 
                headless=self.headless,
                viewport=self.config.get("resolution", {"width": 1280, "height": 720}),
                user_agent="ArchonIntegratedScout/39.1 (scenario-twin)",
                record_video_dir=record_dir,
                record_video_size=record_size
            )
            pg = await ctx.new_page()
            pg.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
            pg.on("console", lambda msg: print(f"🖥️ [Browser Console] {msg.type}: {msg.text}"))
            pg.on("pageerror", lambda err: print(f"❌ [Browser Page Error] {err}"))
            
            # Auth
            auth = self.config.get("auth", {})
            if auth:
                try:
                    await pg.goto(f"{url}{auth.get('url', '/#/auth')}", wait_until="domcontentloaded", timeout=30000)
                    try:
                        await pg.wait_for_selector('input[type="email"]', timeout=5000)
                        await pg.fill('input[type="email"]', auth["user"])
                        pwd = os.getenv(auth.get("password_env", ""), auth.get("password", "qwer45tyuiop"))
                        await pg.fill('input[type="password"]', pwd)
                        await pg.click('button[type="submit"]')
                        await asyncio.sleep(3)
                    except Exception:
                        pass # Already logged in
                except Exception as e:
                    print(f"❌ [Scout-Runner] Auth failed: {e}")
                    return f"WORKFLOW_FAILURE: Auth failed - {e}", None

            # Execute steps
            steps = self.config.get("steps", [])
            for i, step in enumerate(steps):
                action = step.get("action")
                print(f"🔄 [Scout-Runner] Step {i+1}: {action}")
                try:
                    if action == "goto":
                        await pg.goto(f"{url}{step['url']}", wait_until=step.get("wait_until", "load"), timeout=step.get("timeout", 30000))
                    elif action == "click":
                        if "wait_selector" in step:
                            await pg.wait_for_selector(step["selector"], timeout=10000)
                        await pg.locator(step["selector"]).first.click()
                    elif action == "fill":
                        val = step["value"].replace("{TIMESTAMP}", str(int(time.time())))
                        await pg.fill(step["selector"], val)
                    elif action == "select_option":
                        await pg.select_option(step["selector"], step["value"])
                    elif action == "sleep":
                        await asyncio.sleep(step["duration"] / 1000.0)
                    elif action == "wait_selector":
                        await pg.wait_for_selector(step["selector"], timeout=step.get("timeout", 30000))
                    elif action == "reload":
                        await pg.reload()
                except Exception as e:
                    print(f"❌ [Scout-Runner] Step {i+1} failed: {e}")
                    await pg.screenshot(path="failed_step.png", full_page=True)
                    return f"WORKFLOW_FAILURE: Step {i+1} ({action}) failed - {e}", None

            # Analysis
            analysis_config = self.config.get("analysis", {})
            res_analysis = "WORKFLOW_SUCCESS: Steps completed without AI verification."
            
            if analysis_config:
                if analysis_config.get("type") == "static":
                    res_analysis = analysis_config.get("success_message", "WORKFLOW_SUCCESS")
                else:
                    img_bytes = None
                    if analysis_config.get("screenshot", False):
                        print("📸 [Scout-Runner] Capturing screenshot for AI...")
                        img_bytes = await pg.screenshot(full_page=True)
                        with open("./.twin/diagnostics/scenario_screenshot.png", "wb") as f:
                            f.write(img_bytes)
                    
                    extract_len = analysis_config.get("dom_extract_length", 1000)
                    txt = await pg.evaluate(f"() => document.body.innerText.substring(0, {extract_len})")
                    
                    sys_prompt = analysis_config.get("system_prompt", "Return [WORKFLOW_SUCCESS] if looks ok.")
                    
                    contents = [f"[DOM Context]: {txt}"]
                    if img_bytes:
                        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
                        
                    res_analysis = await analyze_with_retry(self.client, self.target_model, contents, sys_prompt)
                    print(f"✅ [Scout-Runner] AI Analysis complete.")
            
            video_path = None
            if self.is_record and pg.video:
                video_path = await pg.video.path()
                print(f"📹 [Scout-Runner] WebM Video recorded at: {video_path}")
            
            await ctx.close()
            await browser.close()
            
            return res_analysis, video_path


async def run_scout_session():
    args = parse_args()
    is_headless = args.headless.lower() == "true"
    mode = args.mode.lower()
    
    # Phase 4.6.46 Hardening: Wait for backend hot-reload stability
    if mode == "audit":
        print("⏳ [Scout] Cooling down 15s for backend stability (Anti-503)...")
        await asyncio.sleep(15)
    
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

    if mode == "audit":
        reality_map = {}
        for p_email in ["alice@archon.com", "bob@archon.com", "charlie@archon.com", "admin@archon.com", "dev.bot@archon.com"]:
            reality_map[p_email] = await get_workflow_snapshot(p_email)

        personas = [
            {"email": "alice@archon.com", "url": "/marketing", "selector": "ul, table, .grid-cols-1", "name": "Alice (Sales)"},
            {"email": "bob@archon.com", "url": "/brand", "selector": ".bg-purple-50, aside div.flex-1.overflow-y-auto > div", "name": "Bob (Marketing)"},
            {"email": "charlie@archon.com", "url": "/nexus", "selector": "canvas, .recharts-responsive-container", "name": "Charlie (Manager Nexus)"},
            {"email": "admin@archon.com", "url": "/admin", "selector": "h1, .admin-panel", "name": "David Howard (Admin)"},
            {"email": "dev.bot@archon.com", "url": "/dashboard", "selector": "ul, table, .card", "name": "DevBot (Agent)"}
        ]

        from cookie_injector import KeychainBypassCookieInjector
        
        global_report = []
        async with async_playwright() as p:
            for p_config in personas:
                safe_name = p_config["name"].split()[0].lower()
                browser, ctx = await KeychainBypassCookieInjector.create_keychain_bypass_context(
                    p, 
                    headless=is_headless,
                    state_path="NONEXISTENT_STATE_TO_FORCE_CLEAN",  # Bypasses any pre-saved state to force clean programmatic login
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=f"ArchonIntegratedScout/3.9.1 ({safe_name})"
                )
                pg = await ctx.new_page()
                res = await inspect_and_analyze(pg, p_config, reality_map, client, target_model, mission_prompt)
                global_report.append(res)
                await ctx.close()
                await browser.close()
                
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

    if args.scenario:
        print(f"🚀 [Scout] Entering SCENARIO mode using {args.scenario}...")
        is_record = args.record.lower() == "true"
        runner = YAMLScenarioRunner(args.scenario, client, target_model, is_record, is_headless)
        res_analysis, video_path = await runner.run()
        
        # Post-processing video
        if is_record and video_path:
            is_success = "WORKFLOW_SUCCESS" in res_analysis
            if is_success:
                print("🎉 Workflow success! Processing recorded video...")
                import subprocess
                try:
                    proc_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "process_marketing_video.py"))
                    subprocess.run(
                        [sys.executable, proc_script, "--video", video_path],
                        check=True
                    )
                    print("📹 [Scout] Video post-processing executed successfully.")
                except Exception as ve:
                    print(f"⚠️ [Scout] Video post-processing failed: {ve}")
            else:
                print("❌ Workflow failed! Deleting temp recording video...")
                if os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                        print("🗑️ Removed failed recording video.")
                    except Exception as ve:
                        pass
        
        report_text = f"# Digital Twin Scenario Report\n\n## Scenario Configuration\n{args.scenario}\n\n## Action Verification\n{res_analysis}\n"
        report_dir = "./.twin/diagnostics"
        os.makedirs(report_dir, exist_ok=True)
        report_path = f"{report_dir}/report_scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, "w", encoding="utf-8") as f: f.write(report_text)
        
        print(f"📄 [Scout] Scenario Report saved: {report_path}")
        final_type = "WORKFLOW_FAILURE" if "WORKFLOW_FAILURE" in report_text or "PARITY_MISMATCH" in report_text else "WORKFLOW_SUCCESS"
        await log_twin_diagnosis(report_text, final_type)
        return

if __name__ == "__main__":
    asyncio.run(run_scout_session())
