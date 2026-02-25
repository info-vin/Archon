import asyncio
import os
import base64
from datetime import datetime
from supabase import create_client, Client
from playwright.async_api import async_playwright
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

async def get_mission_from_db():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    prompt_key = os.getenv("SCOUT_PROMPT_KEY", "twin_scout_mission")
    try:
        supabase: Client = create_client(url, key)
        res = supabase.table("archon_prompts").select("prompt").eq("prompt_name", prompt_key).execute()
        return res.data[0]["prompt"] if res.data else "Standard UI Audit."
    except Exception as e:
        print(f"⚠️ DB Fetch Failed: {e}")
        return "Standard Audit."

async def run_scout_session():
    print("🔄 啟動 Digital Twin Scout (原生 Playwright + Gemini Vision)...")
    mission = await get_mission_from_db()
    print(f"📋 目標指令: {mission}")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
        
    if not api_key:
        print("❌ Cannot find GEMINI_API_KEY or GOOGLE_API_KEY in environment variables.")
        return
        
    # Prevent Langchain from picking up an expired GOOGLE_API_KEY if GEMINI_API_KEY is preferred
    if "GOOGLE_API_KEY" in os.environ and os.getenv("GEMINI_API_KEY"):
        del os.environ["GOOGLE_API_KEY"]

    report_dir = "./.twin/diagnostics"
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"{report_dir}/report_{timestamp}.md"
    
    results = []

    try:
        async with async_playwright() as p:
            # 啟動 Chromium 瀏覽器
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = await browser.new_context()
            page = await context.new_page()

            # --- Target 1: Admin UI (3737) ---
            print("📍 正在巡檢 Admin UI (http://archon-ui:3737)...")
            await page.goto("http://archon-ui:3737")
            try:
                # 等待 React 掛載與頁面穩定
                await page.wait_for_selector('#root > *', timeout=30000)
                await asyncio.sleep(2)  # 物理緩衝
                b64_admin = base64.b64encode(await page.screenshot()).decode("utf-8")
                dom_admin = await page.evaluate("() => document.body.innerText.substring(0, 1000)") # 字串截斷
                results.append({"name": "Admin UI", "image": b64_admin, "text": dom_admin})
                print("✅ Admin UI 截圖成功")
            except Exception as e:
                print(f"⚠️ Admin UI 截圖失敗: {e}")

            # --- Target 2: EndUser UI (5173 Login Flow) ---
            print("📍 正在巡檢 EndUser UI (http://enduser-ui:5173/#/auth)...")
            await page.goto("http://enduser-ui:5173/#/auth")
            try:
                await page.wait_for_selector('input[type="email"]', timeout=30000)
                await page.fill('input[type="email"]', "alice@archon.com")
                await page.fill('input[type="password"]', "qwer45tyuiop")
                
                # 點擊登入按鈕並等待導航
                await page.click('button[type="submit"]')
                print("⏳ 等待登入後跳轉與渲染...")
                
                # 等待跳轉後的主要介面出現 (假設有特定 sidebar 或 root 下的子元素)
                await page.wait_for_selector('#root > *', timeout=30000)
                await asyncio.sleep(3) # 給予網路載入 Dashboard 的時間
                
                b64_user = base64.b64encode(await page.screenshot()).decode("utf-8")
                dom_user = await page.evaluate("() => document.body.innerText.substring(0, 1000)")
                results.append({"name": "EndUser UI", "image": b64_user, "text": dom_user})
                print("✅ EndUser UI 截圖成功")
            except Exception as e:
                print(f"⚠️ EndUser UI 登入或截圖失敗: {e}")

            await browser.close()
            
        if not results:
            print("❌ 沒有收集到任何 UI 截圖，退出。")
            return
            
        print("🚀 將擷取的畫面送交 Gemini 分析...")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)
        
        # 準備多模態訊息 (Multimodal Message)
        message_content = [
            {"type": "text", "text": f"你是一位強悍的 UX/UI 診斷工程師 Digital Twin Scout。\n\n使用者的測試目標：\"{mission}\"\n\n請根據以下提供的網頁截圖，分析這兩個 UI 的狀態，並產出一份 Markdown 格式的中文診斷報告。報告應包含：1. 觀察到的介面狀態 (有無空洞、錯誤訊息) 2. 是否符合目標預期。"}
        ]
        
        for ui in results:
            message_content.append({"type": "text", "text": f"--- {ui['name']} 畫面內容參考: {ui['text']} ---"})
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{ui['image']}"}
            })
            
        human_msg = HumanMessage(content=message_content)
        
        response = await llm.ainvoke([human_msg])
        print("✅ Gemini 分析完成!")
        
        # Output final result to report
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Twin Scout Agent Report (Vision API)\n")
            f.write(f"- **Time**: {datetime.now().isoformat()}\n")
            f.write(f"- **Mission Prompt**: {mission}\n\n")
            f.write(f"## 視覺診斷結果\n\n")
            f.write(response.content)
            
        print(f"📄 報告已儲存至: {report_path}")

    except Exception as e:
        print(f"❌ 嚴重故障 (Scout Crash): {e}")

if __name__ == "__main__":
    asyncio.run(run_scout_session())
