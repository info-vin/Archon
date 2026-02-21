import asyncio
import os
from datetime import datetime
from browser_use import Agent, Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI

# 初始化 Gemini 2.0 Flash (高效能、低成本視覺模型)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# 瀏覽器持久化配置 (對齊 Docker 掛載路徑)
config = BrowserConfig(
    headless=True,
    chrome_instance_path='/usr/bin/google-chrome',
    extra_chromium_args=[f'--user-data-dir=/app/user_data']
)

async def main():
    browser = Browser(config=config)
    
    task = """
    1. 前往 http://enduser-frontend:5173。
    2. 確認是否已透過 Google 帳號登入端點。
    3. 模擬用戶：嘗試建立一個新任務並觀察 UI 流程，記錄任何 UI 遮擋或操作不順暢之處。
    4. 接下來，前往 http://archon-frontend:3737。
    5. 觀察並確認系統狀態與 UI，無需登入。
    6. 產出包含 Mermaid 流程圖的 Markdown 診斷報告，統整兩個網站的健康狀況。
    """

    agent = Agent(task=task, llm=llm, browser=browser)
    result = await agent.run()
    
    # 寫入專案路徑供 Antigravity RAG 學習
    report_path = f"./.twin/diagnostics/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"✓ 報告已生成: {report_path}")
    await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
