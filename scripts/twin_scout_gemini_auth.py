import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
import base64

async def main():
    print("🌟 [MISSION] Gemini Image Generation - kwok022 Identity Check")
    
    browser_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.browser_data'))
    
    # 清理鎖定文件
    for lock in ["SingletonLock", "SingletonSocket", "SingletonCookie", "Lock"]:
        f = os.path.join(browser_data_dir, lock)
        if os.path.exists(f):
            os.remove(f)
            print(f"🔓 Removed {lock}.")

    async with async_playwright() as p:
        print(f"📂 Launching Browser Context: {browser_data_dir}")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=browser_data_dir,
            headless=False,
            channel="chrome",
            ignore_default_args=["--enable-automation"],
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        page = await context.new_page()
        page.set_default_timeout(60000)
        
        try:
            print("🚀 Navigating to Gemini...")
            await page.goto("https://gemini.google.com/", wait_until="domcontentloaded")
            
            print("\n=======================================================")
            print("🟢 視窗已開啟！")
            print("⚠️ 如果您看到登入畫面，請現在手動登入您的 kwok022 帳號。")
            print("⏳ 腳本將在此等待 (最多 3 分鐘)... 登入完成後腳本會自動接手！")
            print("=======================================================\n")

            # 動態等待主對話框出現 (代表登入成功且介面已載入)
            textarea = await page.wait_for_selector('div[contenteditable="true"]', timeout=180000)
            
            if not textarea:
                 print("❌ Failed to find prompt textarea after 3 minutes.")
                 return
                 
            print("✅ Main prompt area detected! Automation resuming...")

            # 1. 檢查身份 kwok022
            print("🔍 Verifying User Identity (kwok022)...")
            content = await page.content()
            if "kwok022" in content:
                print("✅ Confirmed: 'kwok022' detected in session.")
            else:
                print("⚠️ Warning: 'kwok022' not found in page text. Please check login manually.")
            
            # 2. 點擊 "工具 (Tools)" 並選取 "建立圖片"
            print("🛠️ Searching for 'Tools' -> 'Create Image' (or Banana)...")
            
            # 試圖點擊選單或擴充功能圖示
            menu_selectors = [
                "text=工具", "text=Tools", "text=擴充功能", "text=Extensions",
                "button[aria-label*='工具']", "button[aria-label*='Tools']",
                "a[href*='/extensions']"
            ]
            
            for sel in menu_selectors:
                try:
                    target = await page.query_selector(sel)
                    if target:
                        print(f"👉 Found Tools/Menu: {sel}. Clicking...")
                        await target.click()
                        await asyncio.sleep(2)
                        break
                except:
                    continue

            # 尋找 建立圖片 或 Banana
            image_tool_selectors = [
                "text=建立圖片", "text=Create Image", "text=Banana", "text=Imagen",
                "a:has-text('建立圖片')", "a:has-text('Banana')"
            ]
            
            tool_found = False
            for sel in image_tool_selectors:
                try:
                    tool = await page.query_selector(sel)
                    if tool:
                        print(f"✅ Found Image Tool: {sel}. Clicking...")
                        await tool.click()
                        tool_found = True
                        break
                except:
                    continue
            
            if not tool_found:
                print("⚠️ Could not find specific tool menu item. Proceeding to main prompt.")

            await asyncio.sleep(5)
            
            # 3. 輸入提示詞
            prompt_text = "我想用 banana 畫一張有科技感的現代藝術設計圖，可以當成 blog 的示意圖"
            print(f"✍️ Typing prompt: {prompt_text}")
            
            # 尋找主要輸入框
            textarea = await page.wait_for_selector('div[contenteditable="true"]', timeout=15000)
            if textarea:
                await textarea.fill(prompt_text)
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")
                print("🚀 Prompt submitted!")
            else:
                print("❌ Failed to find prompt textarea.")

            print("⏳ Waiting for image generation (45s)...")
            await asyncio.sleep(45)
            
            # 4. 產出結果截圖
            timestamp = datetime.now().strftime('%H%M%S')
            final_path = f"./.twin/diagnostics/banana_final_{timestamp}.png"
            await page.screenshot(path=final_path, full_page=True)
            print(f"📸 MISSION COMPLETE! Result saved to: {final_path}")
            print("💡 Since API Quota is reached, please inspect the screenshot manually.")

        except Exception as e:
            print(f"❌ Error during mission: {e}")
            await page.screenshot(path="./.twin/diagnostics/banana_crash_report.png")
        finally:
            await context.close()
            print("💾 Context saved and closed.")

if __name__ == "__main__":
    asyncio.run(main())
