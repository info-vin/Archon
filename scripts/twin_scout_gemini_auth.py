import asyncio
import os
from dotenv import load_dotenv

# Load Archon/.env automatically
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ConfigDict
from browser_use import Agent, Browser, BrowserConfig

class TwinLLM(ChatGoogleGenerativeAI):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @property
    def provider(self):
        return "google"

async def main():
    print("🌟 [PROBE] Starting Gemini Auth Test (Browser-Use Persistent Context)...")
    
    # Optional: we run locally, ensure API key is available
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Missing API Key in environment variables. Please set GEMINI_API_KEY=...")
        return
        
    # FORCE overwrite to ensure LangChain uses the correct key
    os.environ['GOOGLE_API_KEY'] = api_key

    print("✅ Initializing LLM...")
    llm = TwinLLM(model="gemini-2.5-flash", api_key=api_key)
    llm.model_name = "gemini-2.5-flash"
    
    print("✅ Initializing Persistent Browser Context...")
    # By using `user_data_dir` in BrowserConfig, Playwright will load the profile
    # from our project's .browser_data (which was used previously to log in).
    browser_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.browser_data'))
    browser = Browser(
        config=BrowserConfig(
            headless=False,
            user_data_dir=browser_data_dir
        )
    )
    
    prompt = (
        "前往 Google Gemini (https://gemini.google.com/)，檢查是否已登入。"
        "如果未登入，請等待或報告需要人類協助登入；"
        "如果已登入，請先在畫面上 (可能是左側選單或 Gems 列表) 尋找並點選名叫 'Banana' 的工具或 Gem。"
        "確定進入 Banana 的對話模式後，在對話框輸入提示詞：'我想用 banana 畫一張有科技感的現代藝術設計圖，可以當成 blog 的示意圖'，"
        "送出對話後，等待結果生成並回傳結果摘要。"
    )

    print("✅ Initializing Agent...")
    agent = Agent(
        task=prompt,
        llm=llm,
        browser=browser
    )
    
    try:
        print("🚀 Running Agent...")
        result = await agent.run()
        print("✅ [SUCCESS] Agent operation completed!")
        print(f"📊 Result: {result.final_result()}")
        print("⏸️ 已經完成指令，現在暫停 120 秒讓您檢視瀏覽器畫面...")
        await asyncio.sleep(120)
    except Exception as e:
        print(f"❌ [FAILED] Agent crashed: {e}")
    finally:
        await browser.close()
        print(f"💾 Browser state saved to: {browser_data_dir}")

if __name__ == "__main__":
    asyncio.run(main())
