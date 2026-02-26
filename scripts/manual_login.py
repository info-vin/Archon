import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    browser_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.browser_data'))
    print(f"📂 Launching Browser Context: {browser_data_dir}")
    
    # 清理鎖定文件以確保順利啟動
    for lock in ["SingletonLock", "SingletonSocket", "SingletonCookie", "Lock"]:
        f = os.path.join(browser_data_dir, lock)
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"🔓 Removed {lock}.")
            except:
                pass

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=browser_data_dir,
            headless=False,  # 必須設為 False 讓您看見視窗
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await context.new_page()
        print("🚀 Navigating to Gemini...")
        await page.goto("https://gemini.google.com/")
        
        print("")
        print("=======================================================")
        print("🟢 瀏覽器已開啟！請在跳出的視窗中：")
        print("1. 點擊 'Sign in'")
        print("2. 使用您的 kwok022@gmail.com 帳號登入")
        print("3. 完成登入後，請等待視窗自動關閉。")
        print("⏳ 您有 3 分鐘的時間完成登入程序...")
        print("=======================================================")
        print("")
        
        # 等待 180 秒讓使用者操作
        await asyncio.sleep(180)
        
        print("💾 時間到！正在儲存 Session 並關閉瀏覽器...")
        await context.close()
        print("✅ Session 更新完成。")

if __name__ == "__main__":
    asyncio.run(main())
