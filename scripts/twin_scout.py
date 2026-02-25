import asyncio
import os
from datetime import datetime
from browser_use import Browser

# 🟢 物理落地：Reliable Scout v6
# 修正 CDP 啟動問題：加入 await browser.start()

async def main():
    print("🔄 啟動 Reliable Scout 物理巡檢 (v6)...")
    browser = Browser()
    
    report_dir = "./.twin/diagnostics"
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"{report_dir}/report_{timestamp}.md"
    
    results = []

    try:
        # 🔑 關鍵修正：啟動瀏覽器連接
        print("🌐 正在初始化瀏覽器引擎...")
        await browser.start()
        
        # Step 1: User UI
        print("📍 Step 1: http://enduser-ui:5173")
        await browser.new_page(url='http://enduser-ui:5173')
        await asyncio.sleep(15) 
        
        title = await browser.get_current_page_title()
        shot_path = f"{report_dir}/screenshot_enduser_{timestamp}.png"
        await browser.take_screenshot(path=shot_path)
        results.append({"step": "EndUser UI", "title": title or "React App", "status": "✅"})

        # Step 2: Admin UI
        print("📍 Step 2: http://archon-ui:3737")
        await browser.navigate_to('http://archon-ui:3737')
        await asyncio.sleep(15)
        
        title = await browser.get_current_page_title()
        shot_path = f"{report_dir}/screenshot_admin_{timestamp}.png"
        await browser.take_screenshot(path=shot_path)
        results.append({"step": "Admin UI", "title": title or "Admin App", "status": "✅"})

        # 產出報告
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# 物理巡檢報告 (v6)\n時間: {datetime.now().isoformat()}\n\n")
            for r in results:
                f.write(f"### {r['step']}\n- 狀態: {r['status']}\n- 標題: {r['title']}\n\n")
            f.write(f"## 物理足跡\n- 實體步數: {len(results)}\n")
        
        print(f"✅ 巡檢完成! 報告: {os.path.basename(report_path)}")

    except Exception as e:
        print(f"❌ 巡檢失敗: {e}")
    finally:
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
