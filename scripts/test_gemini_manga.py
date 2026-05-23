import asyncio
import os
import sys
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    print("🌟 [TEST] Gemini Automation - Generating Lily blooming comic...")
    
    # Resolve the browser data directory path
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
        
        # Launch Chrome using the persistent profile to reuse existing login session
        context = await p.chromium.launch_persistent_context(
            user_data_dir=browser_data_dir,
            headless=False,  # Headed mode so you can see it and log in if needed
            channel="chrome",  # Use your system's Google Chrome
            ignore_default_args=["--enable-automation"],
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox', 
                '--disable-blink-features=AutomationControlled',
                '--password-store=basic'
            ]
        )
        
        page = await context.new_page()
        page.set_default_timeout(90000)
        
        try:
            print("🚀 Navigating to Gemini web app...")
            await page.goto("https://gemini.google.com/", wait_until="domcontentloaded")
            
            print("\n=======================================================")
            print("🟢 Browser window opened!")
            print("🔍 Checking authentication status...")
            print("=======================================================\n")
            
            await asyncio.sleep(5)  # Allow page to fully load and run scripts
            
            # Look for sign in buttons (Traditional Chinese and English variants)
            login_buttons = await page.locator("a:has-text('登入'), button:has-text('登入'), a:has-text('Sign in'), button:has-text('Sign in'), a[href*='accounts.google.com']").all()
            
            need_login = False
            for btn in login_buttons:
                if await btn.is_visible():
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
                    buttons = await page.locator("a:has-text('登入'), button:has-text('登入'), a:has-text('Sign in'), button:has-text('Sign in'), a[href*='accounts.google.com']").all()
                    still_need_login = False
                    for btn in buttons:
                        if await btn.is_visible():
                            still_need_login = True
                            break
                    
                    if not still_need_login:
                        # Double check by making sure the textarea is present
                        try:
                            textarea = await page.wait_for_selector('div[contenteditable="true"]', timeout=5000)
                            if textarea:
                                print("🎉 [AUTHENTICATED] Login detected! Proceeding to prompt injection...")
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
            
            # Wait for prompt input box
            textarea = await page.wait_for_selector('div[contenteditable="true"]', timeout=30000)
            
            if not textarea:
                print("❌ Prompt input box not found. Exiting.")
                return
                
            print("✅ Prompt input area detected. Injecting prompt...")
            
            # Focus on the input box
            await textarea.focus()
            await asyncio.sleep(1)
            
            # Type prompt
            prompt_text = "可以製作8 秒 百合開花的漫畫?"
            print(f"✍️ Typing: {prompt_text}")
            await textarea.fill(prompt_text)
            await asyncio.sleep(1)
            
            # Submit by pressing Enter
            print("🚀 Submitting prompt...")
            await page.keyboard.press("Enter")
            
            # Wait for generation to complete (usually 45-60 seconds for complex media prompts)
            print("⏳ Waiting for Gemini to generate output (60 seconds)...")
            await asyncio.sleep(60)
            
            # Capture final screenshot
            scratch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scratch'))
            os.makedirs(scratch_dir, exist_ok=True)
            screenshot_path = os.path.join(scratch_dir, "manga_test_result.png")
            
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 SUCCESS! Screenshot saved to: {screenshot_path}")
            
        except Exception as e:
            print(f"❌ Error during automation: {e}")
            # Try to save crash report screenshot
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
