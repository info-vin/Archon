import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 監聽所有網路請求
        page.on("request", lambda request: print(f"Request: {request.url} | Headers: {request.headers.get('x-user-role', 'MISSING')}") if "/api/marketing/leads" in request.url else None)

        await page.goto("http://localhost:5173/#/auth")
        await page.fill('input[type="email"]', 'alice@archon.com')
        await page.fill('input[type="password"]', 'qwer45tyuiop')
        await page.click('button[type="submit"]')
        await asyncio.sleep(5)
        
        # 觸發資料讀取
        await page.goto("http://localhost:5173/#/marketing")
        await asyncio.sleep(5)
        
        await browser.close()

asyncio.run(inspect())
