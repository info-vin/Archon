import asyncio
from playwright.async_api import async_playwright

async def inspect_persona(email, password, url_suffix, name):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # 存取登入頁面
        await page.goto("http://localhost:5173/#/auth")
        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', password)
        await page.click('button[type="submit"]')
        await asyncio.sleep(5)
        
        # 進入目標頁面
        await page.goto(f"http://localhost:5173/#{url_suffix}")
        await asyncio.sleep(5)
        
        # 抓取 DOM
        content = await page.content()
        print(f"--- Persona: {name} ---")
        # 檢查 Alice 的 Assignee 與 Bob 的任務列表
        if "Alice" in name:
            print("Alice content snippet (assignee check):")
            print(content[:2000])
        elif "Bob" in name:
            print("Bob content snippet (task list check):")
            print(content[:2000])
        
        await browser.close()

async def main():
    await inspect_persona("alice@archon.com", "qwer45tyuiop", "marketing", "Alice (Sales)")
    await inspect_persona("bob@archon.com", "qwer45tyuiop", "brand", "Bob (Marketing)")

asyncio.run(main())
