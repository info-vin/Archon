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

# TODO (Phase 4.6.9): 實作 Agent 子目錄 Session 隔離，避免多人同時使用 Chrome 導致 SingletonLock 衝突。
# TODO (Phase 4.6.9): 實作基於 Gemini Vision 判定結果的動態評分系統。

def parse_args():
    parser = argparse.ArgumentParser(description="Digital Twin Scout v27 - Back to Origins")
    parser.add_argument("--mode", type=str, default="both", choices=["audit", "action", "both"])
    parser.add_argument("--headless", type=str, default="true")
    return parser.parse_args()

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
            "details": {"agent_name": "TwinScout", "xp_change": xp_change, "v": "v27"}
        }).execute()
    except:
        pass

async def perform_banana_action(page, mission_text):
    print(f"🚀 [ACTION] 啟動 Gemini 任務...")
    try:
        await page.goto("https://gemini.google.com/", wait_until="domcontentloaded")
        await page.wait_for_selector('div[contenteditable="true"]', timeout=180000)
        
        # 工具操作
        menu_selectors = ["button[aria-label*='工具']", "text=工具", "text=Tools"]
        for sel in menu_selectors:
            target = await page.query_selector(sel)
            if target:
                await target.click()
                await asyncio.sleep(2)
                break

        tool_selectors = ["text=Banana", "text=建立圖片", "text=Create Image"]
        for sel in tool_selectors:
            tool = await page.query_selector(sel)
            if tool:
                await tool.click()
                await asyncio.sleep(5)
                break

        # 重新定位並送出
        textarea = await page.wait_for_selector('div[contenteditable="true"]', timeout=15000)
        await textarea.fill(mission_text)
        await page.keyboard.press("Enter")
        print("✍️ 指令已送出，等待繪製 (45s)...")
        await asyncio.sleep(45)
        
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        return True
    except Exception as e:
        print(f"❌ Action 失敗: {e}")
        return False

async def run_scout_session():
    args = parse_args()
    is_headless = args.headless.lower() == "true"
    
    # 確保 API Key 優先級
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if "GOOGLE_API_KEY" in os.environ and os.getenv("GEMINI_API_KEY"):
        del os.environ["GOOGLE_API_KEY"]

    all_results = []
    
    async with async_playwright() as p:
        # --- Audit Stage ---
        if args.mode in ["audit", "both"]:
            audit_dir = os.path.abspath("./.browser_data/temp_audit")
            if os.path.exists(audit_dir): shutil.rmtree(audit_dir, ignore_errors=True)
            os.makedirs(audit_dir, exist_ok=True)
            
            ctx = await p.chromium.launch_persistent_context(user_data_dir=audit_dir, headless=is_headless, args=['--no-sandbox', '--disable-setuid-sandbox'])
            pg = await ctx.new_page()
            
            # Admin UI
            try:
                url = os.getenv("ADMIN_UI_URL", "http://archon-ui:3737")
                await pg.goto(url, wait_until="domcontentloaded", timeout=30000)
                await pg.wait_for_selector('#root > *', timeout=30000)
                await asyncio.sleep(2)
                txt = await pg.evaluate("() => document.body.innerText.substring(0, 1000)")
                all_results.append({"name": "Admin UI", "image": base64.b64encode(await pg.screenshot()).decode("utf-8"), "text": txt})
            except: pass

            # EndUser UI (含登入)
            try:
                url = os.getenv("ENDUSER_UI_URL", "http://enduser-ui:5173")
                await pg.goto(f"{url}/#/auth", wait_until="domcontentloaded", timeout=30000)
                await pg.wait_for_selector('input[type="email"]', timeout=30000)
                await pg.fill('input[type="email"]', "alice@archon.com")
                await pg.fill('input[type="password"]', "qwer45tyuiop")
                await pg.click('button[type="submit"]')
                await pg.wait_for_selector('#root > *', timeout=30000)
                await asyncio.sleep(3)
                txt = await pg.evaluate("() => document.body.innerText.substring(0, 1000)")
                all_results.append({"name": "EndUser UI", "image": base64.b64encode(await pg.screenshot()).decode("utf-8"), "text": txt})
            except: pass
            
            await ctx.close()

        # --- Action Stage ---
        if args.mode in ["action", "both"]:
            root_dir = os.path.abspath("./.browser_data")
            for lock in ["SingletonLock", "SingletonSocket"]:
                f = os.path.join(root_dir, lock)
                if os.path.exists(f): os.remove(f)

            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=root_dir, headless=is_headless,
                ignore_default_args=["--enable-automation"],
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
            )
            pg = await ctx.new_page()
            
            mission = await get_mission_from_db("banana_mission")
            success = await perform_banana_action(pg, mission)
            if success:
                img = base64.b64encode(await pg.screenshot(full_page=True)).decode("utf-8")
                all_results.append({"name": "Gemini_Action", "image": img})
            
            await ctx.close()

    if all_results:
        print("🚀 調用 Gemini Vision 產生最終報告...")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)
        mission_desc = await get_mission_from_db("twin_scout_mission")
        
        msg_parts = [{"type": "text", "text": f"你是一位強悍的 UX/UI 診斷工程師 Digital Twin Scout。\n任務目標：\"{mission_desc}\"\n請誠實診斷：1. 內部 UI 是否健康？ 2. Gemini 截圖中是否真的畫出圖了？"}]
        for r in all_results:
            info = f"\n--- 截圖：{r['name']} ---"
            if "text" in r: info += f"\n[畫面內容擷取]: {r['text']}"
            msg_parts.append({"type": "text", "text": info})
            msg_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{r['image']}"}})
            
        response = await llm.ainvoke([HumanMessage(content=msg_parts)])
        
        # 【恢復歷史規範】：report_{timestamp}.md
        report_dir = "./.twin/diagnostics"
        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"{report_dir}/report_{timestamp}.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Twin Scout Agent Report\n- **Time**: {datetime.now().isoformat()}\n\n")
            f.write(response.content)
            f.write("\n\n---\n**診斷人：** Digital Twin Scout")
            
        print(f"📄 報告已存至歷史規範路徑: {report_path}")
        await log_agent_xp("Full session finished.")

if __name__ == "__main__":
    asyncio.run(run_scout_session())
