import asyncio
from playwright.async_api import async_playwright

async def check_sidebar():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🚀 [Check] Attempting Bob Login at http://localhost:5173")
        await page.goto("http://localhost:5173/auth")
        
        # 1. Perform Login
        await page.fill('input[type="email"]', "bob@archon.com")
        await page.fill('input[type="password"]', "qwer45tyuiop")
        await page.click('button:has-text("Sign In")')
        
        # 2. Wait for Sidebar
        await page.wait_for_selector('nav', timeout=10000)
        await asyncio.sleep(2) # Ensure hydration
        
        # 3. Extract Sidebar Items
        items = await page.eval_on_selector_all('nav li span', 'elements => elements.map(el => el.textContent)')
        debug_info = await page.eval_on_selector('div.bg-indigo-500', 'el => el.textContent')
        
        print(f"--- BOB REALITY CHECK ---")
        print(f"Role/Perms Found: {debug_info.strip()}")
        print(f"Sidebar Items: {items}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_sidebar())
