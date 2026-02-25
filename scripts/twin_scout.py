import asyncio
import os
import base64
from datetime import datetime
from browser_use import Browser
from supabase import create_client, Client

# 🟢 物理落地：數位孿生偵察員 v9 (原始碼對齊版)
# 修正 screenshot 僅回傳 Base64 的問題，實作實體落地存檔
# 滿足 4.6.7 規範 與 雙生系統 DOM 分析需求

async def get_mission_from_db():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    try:
        supabase: Client = create_client(url, key)
        res = supabase.table("archon_prompts").select("prompt").eq("prompt_name", "twin_scout_mission").execute()
        return res.data[0]["prompt"] if res.data else "Standard UI Audit."
    except: return "Standard Audit."

async def main():
    print("🔄 啟動 Reliable Scout v9 (實體原始碼驅動)...")
    mission = await get_mission_from_db()
    
    browser = Browser()
    report_dir = "./.twin/diagnostics"
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"{report_dir}/report_{timestamp}.md"
    
    results = []

    try:
        await browser.start()
        targets = [
            {"name": "EndUser UI", "url": "http://enduser-ui:5173"},
            {"name": "Admin UI", "url": "http://archon-ui:3737"}
        ]

        for target in targets:
            print(f"📍 正在巡檢: {target['url']}")
            page = await browser.new_page()
            await page.goto(target['url'])
            
            # 強制等待 React 渲染 (Vite 背景依賴重優化較慢)
            print(f"⏳ 等待 React Hydration (20s)...")
            await asyncio.sleep(20)
            
            # 1. 深度分析 DOM
            dom_report = await page.evaluate('''() => {
                const root = document.querySelector('#root');
                const headings = Array.from(document.querySelectorAll('h1, h2')).map(h => h.innerText);
                return {
                    root_exists: !!root,
                    root_has_children: root ? root.children.length > 0 : false,
                    headings: headings
                };
            }''')

            # 2. 物理截圖 (手動處理 Base64)
            b64_data = await page.screenshot()
            shot_name = f"screenshot_{target['name'].lower().replace(' ', '_')}_{timestamp}.png"
            shot_path = os.path.join(report_dir, shot_name)
            
            with open(shot_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            
            results.append({
                "name": target['name'],
                "title": await page.get_title(),
                "dom": dom_report,
                "screenshot": shot_name
            })

        # 3. 產出合規報告
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# 孿生系統深度巡檢報告 (v9)\n")
            f.write(f"- **時間**: {datetime.now().isoformat()}\n")
            f.write(f"- **實體原始碼對齊**: Page.screenshot (Base64 Decode) ✅\n\n")
            
            for r in results:
                f.write(f"## {r['name']}\n")
                f.write(f"- **標題**: `{r['title']}`\n")
                f.write(f"- **物理狀態**:\n")
                f.write(f"  - Root 節點: {'🟢 存在' if r['dom']['root_exists'] else '🔴 缺失'}\n")
                f.write(f"  - React 渲染: {'🟢 有內容' if r['dom']['root_has_children'] else '🔴 空白'}\n")
                if r['dom']['headings']:
                    f.write(f"  - 偵測文字: {', '.join(r['dom']['headings'])}\n")
                f.write(f"- **實體證據**: [{r['screenshot']}]({r['screenshot']})\n\n")

        print(f"✅ 巡檢圓滿完成！報告: {os.path.basename(report_path)}")

    except Exception as e:
        print(f"❌ 嚴重故障: {e}")
    finally:
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
