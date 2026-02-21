import asyncio
import os
import sys
from datetime import datetime
from browser_use import Agent, Browser
from langchain_google_genai import ChatGoogleGenerativeAI

# 🟢 物理修正：建立一個 Proxy 類別來繞過所有 LangChain 與 browser-use 的相容性地雷
class LLMProxy:
    def __init__(self, llm):
        self._llm = llm
        # 必須注入 provider
        self.provider = "google"
        # 必須注入 model_name (browser-use 寫死了讀取這個欄位)
        self.model_name = getattr(llm, 'model', 'gemini-2.0-flash')
    
    def __getattr__(self, name):
        return getattr(self._llm, name)
    
    def __setattr__(self, name, value):
        if name in ["_llm", "provider", "model_name"]:
            super().__setattr__(name, value)
        else:
            self.__dict__[name] = value

# 🟢 物理診斷修正：注入 GOOGLE_API_KEY
google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not google_api_key:
    print("❌ 錯誤: 找不到 GOOGLE_API_KEY。")
    sys.exit(1)

# 初始化原始 Gemini 2.0 Flash
raw_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=google_api_key
)

llm = LLMProxy(raw_llm)

async def main():
    # 🟢 物理修正：使用正確的 browser 初始化方式
    browser = Browser()
    
    task = """
    1. 前往 http://enduser-ui:5173 (User FE)。
    2. 確認介面是否正常載入。
    3. 接下來，前往 http://archon-ui:3737 (Admin UI)。
    4. 觀察 RAG 配置面板是否正常顯示。
    5. 產出 Markdown 報告。
    """

    agent = Agent(task=task, llm=llm, browser=browser)
    
    try:
        print("🚀 Twin Scout 正在啟動，這可能需要一分鐘...")
        result = await agent.run()
        
        report_dir = "./.twin/diagnostics"
        os.makedirs(report_dir, exist_ok=True)
        report_path = f"{report_dir}/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(str(result))

        print(f"✅ 診斷完成！報告已生成: {report_path}")
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
    finally:
        # 🟢 物理修正：browser-use 最新版中，Browser 物件不需要手動調用 .close()
        # 或者其名稱已改變。我們改用更安全的方式。
        try:
            if hasattr(browser, 'close'):
                await browser.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
