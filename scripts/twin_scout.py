import asyncio
import os
import sys
import json
from datetime import datetime

# 🟢 物理修正：防禦性匯入
from browser_use import Agent, Browser
try:
    from browser_use.browser.browser import BrowserConfig, BrowserContextConfig
except ImportError:
    BrowserConfig = None
    BrowserContextConfig = None

from langchain_google_genai import ChatGoogleGenerativeAI
from supabase import create_client, Client

# 🟢 物理修正：RobustLLMWrapper (避開 Pydantic 限制)
class RobustLLMWrapper:
    def __init__(self, llm):
        object.__setattr__(self, "_llm", llm)
        object.__setattr__(self, "provider", "google")
        object.__setattr__(self, "model_name", "gemini-2.0-flash")
    def __getattr__(self, name): return getattr(self._llm, name)
    def bind_tools(self, *args, **kwargs): return self._llm.bind_tools(*args, **kwargs)

# 🟢 憑證
google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not google_api_key:
    print("❌ 錯誤: 找不到 GOOGLE_API_KEY。")
    sys.exit(1)

raw_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=google_api_key)
llm = RobustLLMWrapper(raw_llm)

async def get_mission_from_db():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key: return None
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        res = supabase.table("archon_prompts").select("prompt").eq("prompt_name", "twin_scout_mission").execute()
        return res.data[0]["prompt"] if res.data and len(res.data) > 0 else None
    except Exception as e:
        print(f"⚠️ 雲端連線失敗: {e}")
        return None

async def main():
    # 🟢 物理落地修正：徹底禁用擴充功能，解決 items 報錯與啟動超時
    browser_config = None
    if BrowserConfig:
        browser_config = BrowserConfig(
            headless=True,
            disable_security=True,
            # 關閉所有擴充功能，這在 Docker 環境下能極大增加穩定性
            extra_chromium_args=["--disable-extensions", "--no-sandbox"]
        )
    
    browser = Browser(config=browser_config) if browser_config else Browser()
    
    print("🔄 正在載入 David Howard 的巡檢簡報...")
    db_mission = await get_mission_from_db()
    
    # 強制引導前綴
    task = (
        "Navigate to http://enduser-ui:5173. Wait 10 seconds. " + 
        (db_mission or "Analyze and summarize.")
    )

    print(f"🚀 偵察員出發 (隔離模式)...")
    agent = Agent(task=task, llm=llm, browser=browser, use_vision=True)
    
    try:
        history_list = await agent.run()
        print("📡 任務結束，正在產出 Markdown 報告...")
        
        history_data = history_list.model_dump() if hasattr(history_list, 'model_dump') else {}
        report_dir = "./.twin/diagnostics"
        os.makedirs(report_dir, exist_ok=True)
        report_path = f"{report_dir}/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# 孿生系統巡檢報告\n**時間**: {datetime.now().isoformat()}\n\n")
            f.write("## 1. 診斷結論\n")
            
            final_result = history_data.get("final_result")
            if not final_result or final_result == "None":
                all_res = history_data.get("all_results", [])
                if all_res:
                    # 嘗試從最後一個非空的 extracted_content 抓取
                    for res in reversed(all_res):
                        if res.get("extracted_content"):
                            final_result = res["extracted_content"]
                            break
                    if not final_result:
                        final_result = all_res[-1].get("error") or "任務已結束。"
            
            f.write(str(final_result or "巡檢完成。"))
            f.write(f"\n\n## 2. 物理足跡\n- 步數: {len(history_data.get('all_results', []))}\n")

        print(f"✅ 落地成功！報告已生成: {report_path}")
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")
    finally:
        try: await browser.close()
        except: pass

if __name__ == "__main__":
    asyncio.run(main())
