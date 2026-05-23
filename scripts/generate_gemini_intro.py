import asyncio
import os
import sys
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    print("🌟 [GEMINI INTRO GENERATOR] Starting video asset generation pipeline...")
    
    browser_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.browser_data'))
    os.makedirs(browser_data_dir, exist_ok=True)
    
    # Clean up playwright lock files if any
    for lock in ["SingletonLock", "SingletonSocket", "SingletonCookie", "Lock"]:
        f = os.path.join(browser_data_dir, lock)
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"🔓 Cleaned lock file: {lock}")
            except Exception as e:
                print(f"⚠️ Could not remove lock file {lock}: {e}")

    async with async_playwright() as p:
        print(f"📂 Loading persistent browser profile from: {browser_data_dir}")
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir=browser_data_dir,
            headless=False,  # Must be headed for visual and manual authentication
            channel="chrome",
            ignore_default_args=["--enable-automation"],
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox', 
                '--disable-blink-features=AutomationControlled',
                '--password-store=basic'
            ]
        )
        
        page = await context.new_page()
        page.set_default_timeout(180000)
        
        try:
            print("🚀 Navigating to Gemini web app...")
            await page.goto("https://gemini.google.com/", wait_until="domcontentloaded")
            
            print("\n=======================================================")
            print("🟢 Browser window opened!")
            print("🔍 Checking authentication status...")
            print("=======================================================\n")
            
            await asyncio.sleep(6)  # Allow page to fully load and settle
            
            # Find the active login button on page (specifically checking visible text)
            login_buttons = await page.locator("a:has-text('登入'), button:has-text('登入'), a:has-text('Sign in'), button:has-text('Sign in')").all()
            
            need_login = False
            for btn in login_buttons:
                text = await btn.text_content()
                if await btn.is_visible() and ("登入" in text or "Sign in" in text):
                    need_login = True
                    break
                    
            if need_login:
                print("⚠️  [UNAUTHENTICATED] You are NOT logged in to Gemini.")
                print("➡️  PLEASE LOG IN MANUALLY in the opened Chrome window now.")
                print("⏳ The script will wait up to 3 minutes for you to complete the login...")
                
                start_time = datetime.now()
                logged_in = False
                while (datetime.now() - start_time).total_seconds() < 180:
                    await asyncio.sleep(5)
                    # Check if login buttons are still visible
                    buttons = await page.locator("a:has-text('登入'), button:has-text('登入'), a:has-text('Sign in'), button:has-text('Sign in')").all()
                    still_need_login = False
                    for btn in buttons:
                        text = await btn.text_content()
                        if await btn.is_visible() and ("登入" in text or "Sign in" in text):
                            still_need_login = True
                            break
                    
                    if not still_need_login:
                        try:
                            textarea = await page.wait_for_selector('div[contenteditable="true"]', timeout=5000)
                            if textarea:
                                print("🎉 [AUTHENTICATED] Login detected! Proceeding...")
                                logged_in = True
                                break
                        except:
                            pass
                    print("⏳ Still waiting for login...")
                
                if not logged_in:
                    print("❌ Login timeout (3 minutes exceeded). Exiting script.")
                    return
            else:
                print("🎉 [AUTHENTICATED] Reusing existing logged-in session!")
            
            await asyncio.sleep(3) # Wait briefly for UI to adapt

            # ➕ Click 'New Chat' button to clean session context
            new_chat_btn = page.locator("a:has-text('新對話'), button:has-text('新對話'), a:has-text('New chat'), button:has-text('New chat'), [aria-label*='新對話'], [aria-label*='New chat']")
            buttons = await new_chat_btn.all()
            clicked_new_chat = False
            for btn in buttons:
                if await btn.is_visible():
                    print("➕ Clicking 'New Chat' button...")
                    await btn.click()
                    clicked_new_chat = True
                    await asyncio.sleep(3)
                    break
            
            if not clicked_new_chat:
                print("⚠️ Could not click 'New Chat' button. Proceeding directly...")
            
            # Wait for prompt input box
            textarea = await page.wait_for_selector('div[contenteditable="true"]', timeout=30000)
            if not textarea:
                print("❌ Prompt input box not found. Exiting.")
                return
                
            print("✅ Prompt input area detected. Injecting prompt...")
            await textarea.focus()
            await asyncio.sleep(1)
            
            # Type prompt (4-second rose blooming)
            prompt_text = "可以製作4 秒 玫瑰開花的漫畫?"
            print(f"✍️ Typing: {prompt_text}")
            await textarea.fill(prompt_text)
            await asyncio.sleep(1)
            
            # Submit by pressing Enter
            print("🚀 Submitting prompt...")
            await page.keyboard.press("Enter")
            
            # Wait for content generation and check for the download button
            print("⏳ Waiting for Gemini to generate the asset and for download button to appear (up to 2 minutes)...")
            
            download_btn_selector = "button[aria-label*='下載'], button[title*='下載'], button[aria-label*='Download'], button[title*='Download'], a[aria-label*='下載'], a[aria-label*='Download']"
            
            start_gen_time = datetime.now()
            download_btn = None
            while (datetime.now() - start_gen_time).total_seconds() < 120:
                await asyncio.sleep(5)
                # Try to find visible download buttons
                buttons = await page.locator(download_btn_selector).all()
                for btn in buttons:
                    if await btn.is_visible():
                        download_btn = btn
                        break
                if download_btn:
                    print("🎉 Found download button!")
                    break
                print("⏳ Still generating...")
            
            if not download_btn:
                print("⚠️ Download button not detected automatically after 2 minutes.")
                print("📸 Saving a backup screenshot of the result...")
                scratch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scratch'))
                os.makedirs(scratch_dir, exist_ok=True)
                await page.screenshot(path=os.path.join(scratch_dir, "manga_backup_result.png"), full_page=True)
                print("❌ Exiting due to missing download action.")
                return
            
            # Trigger download
            print("📥 Triggering automatic download...")
            output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'enduser-ui-fe', 'public', 'assets', 'videos', 'auto_demos'))
            os.makedirs(output_dir, exist_ok=True)
            
            async with page.expect_download(timeout=60000) as download_info:
                await download_btn.click()
                
            download = await download_info.value
            
            suggested_filename = download.suggested_filename
            ext = os.path.splitext(suggested_filename)[1] or ".mp4"
            target_path = os.path.join(output_dir, f"gemini_intro{ext}")
            
            await download.save_as(target_path)
            print(f"🎉 SUCCESS! Auto-downloaded asset saved to: {target_path}")
            
        except Exception as e:
            print(f"❌ Error during automation: {e}")
            try:
                crash_path = os.path.join(browser_data_dir, "crash_report.png")
                await page.screenshot(path=crash_path)
                print(f"📸 Saved crash screenshot to: {crash_path}")
            except:
                pass
        finally:
            await context.close()
            print("💾 Browser session saved and closed.")

if __name__ == "__main__":
    asyncio.run(main())
