import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ConfigDict
from browser_use import Agent, Browser

class TwinLLM(ChatGoogleGenerativeAI):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @property
    def provider(self):
        return "google"

async def main():
    print("🌟 [PROBE] Starting Gemini 1.5 Pro + Browser-Use Test (Native Google Provider)...")
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Missing API Key in environment variables.")
        return

    print("✅ API Key found. Initializing LLM...")
    llm = TwinLLM(model="gemini-1.5-pro", api_key=api_key)
    # Give browser-use what it expects
    llm.model_name = "gemini-1.5-pro"
    
    browser = Browser()
    
    print("✅ Initializing Agent...")
    agent = Agent(
        task="Go to https://example.com and extract the main heading (h1). Just return the text.",
        llm=llm,
        browser=browser
    )
    
    try:
        print("🚀 Running Agent (this is where schema parsing errors usually happen)...")
        result = await agent.run()
        print("✅ [SUCCESS] Agent completed without schema crash!")
        print(f"📊 Result: {result.final_result()}")
    except Exception as e:
        print(f"❌ [FAILED] Agent crashed: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
