import asyncio
import os

from playwright.async_api import async_playwright


async def check_video_src():
    url = os.getenv("ENDUSER_UI_URL", "http://localhost:5173")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(f"{url}/#/auth")
        await page.fill('input[type="email"]', "bob@archon.com")
        await page.fill('input[type="password"]', "qwer45tyuiop")
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)

        await page.goto(f"{url}/#/brand")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)

        await page.click('button:has-text("Workbench")')
        await asyncio.sleep(2)

        await page.click('h4:has-text("Neogence")')

        # FIX: Use .first to avoid strict mode violation (2 videos found)
        video_locator = page.locator("video").first
        await video_locator.wait_for(timeout=10000)

        src = await video_locator.get_attribute("src")
        print(f"WEB_PATH_SRC={src}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_video_src())
