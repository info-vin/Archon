import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure python folder is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

for p in [".env", "python/.env", "../.env", "../python/.env"]:
    if os.path.exists(p):
        load_dotenv(p)

from src.server.utils import get_supabase_client

async def run_seed():
    print("🧪 Seeding Digital Twin IPA Blog Post into Database...")
    supabase = get_supabase_client()
    
    title = "解密數位雙生與 AI 智慧型流程自動化 (IPA) 在 Archon 的實踐"
    excerpt = "探討如何將 E2E 自動化測試演進為強大的數位雙生模擬器，結合宣告式關卡、視覺裁判與混沌工程，實現系統級的自癒驗證。"
    
    content = """# 解密數位雙生與 AI 智慧型流程自動化 (IPA) 在 Archon 的實踐

在軟體工程與品質工程的演進過程中，如何在高複雜度的多角色非同步系統中維持 100% 的功能正確性，一直是巨大的挑戰。本文將深入探討 Archon 如何透過 **數位雙生 (Digital Twin)** 技術與 **智慧型流程自動化 (IPA, Intelligent Process Automation)** 理念，重構 E2E 測試流程，將傳統脆弱的自動化腳本升級為具備強大自癒與感知能力的模擬器。

---

## 1. 傳統 E2E 測試與 RPA 的硬傷

許多團隊在做自動化測試時，常使用類似 RPA (Robotic Process Automation) 的軟體機器人來模擬人類的點擊與輸入。然而，傳統的 RPA 面臨兩大致命缺陷：
1. **極度脆弱 (Brittle)**：一旦 UI Layout 稍微調整、按鈕位移或 CSS 類別更換，機器人便會因找不到元素而直接崩潰。
2. **缺乏認知能力**：傳統 RPA 無法做主觀判斷。當網路稍微延遲 2 秒或系統跳出異常彈窗時，機器人無法靈活自癒，導致 E2E 測試出現大量「偽陰性 (False Negatives)」報錯。

---

## 2. 智慧型流程自動化 (IPA) 時代的來臨

為了克服上述硬傷，Archon 引入了結合 AI 認知能力與數位雙生狀態映射的 **IPA (Intelligent Process Automation)** 架構。其核心特徵在於：

### A. 語義自癒定位 (Semantic Locators)
捨棄點對點的座標或嚴苛的 DOM 路徑，改用 Playwright 語義層級的 Intent 定位（如 `button:has-text('RETURN')`），即便前端組件重構，只要功能意圖未變，機器人就能自動找到目標。

### B. AI 多模態視覺裁判 (LLM-based Visual Judge)
透過與 `gemini-3.1-flash-lite` 模型的 Native 整合，IPA 機器人能夠在點擊完畢後進行 Full-page 截圖並送入 AI 進行視覺布局校驗。這成功解除了「DOM 節點存在但按鈕其實被覆蓋或透明化」的測試盲區。

### C. 冪等沙盒與狀態自癒 (Idempotent Sandboxing)
每個測試關卡啟動前，自動透過 Python Pre-hook 清理並還原資料庫狀態（如重設權限與狀態），消除了資料殘留與狀態污染引起的干擾。

---

## 3. 關卡式動態模擬器 (Digital Twin Simulator) 設計

受遊戲開發商關卡驗證與自動回放機制的啟發，我們在 Phase 5.4.2 中將這套 IPA 機制擴充成一個支援 **100+ 個微型測試關卡**的動態模擬器：

1. **參數化關卡生成**：透過 `level_generator.py` 動態產生覆蓋 Campaign A（權限對抗）、B（異常網路）、C（輸入邊界）、D（一致性審計）四大維度的關卡腳本。
2. **併發與混沌注入**：模擬器執行器 `simulator_runner.py` 支援 Concurrency=3 的併發運行，並在執行期間隨機注入 API 延遲與 HTTP 500 錯誤，強制對前端的錯誤防禦機制與自癒狀態機進行應力測試。

這套融合了數位雙生、RPA 與 LLM 的自動化底座，不僅大幅節省了測試成本，更確保了 Archon 在快速迭代的 Beta 階段中，核心商業流程的絕對堅固。
"""

    import datetime
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    blog_post = {
        "title": title,
        "excerpt": excerpt,
        "content": content,
        "author_name": "Archon Architect",
        "status": "published",
        "target_brand": "Archon",
        "publish_date": now_str,
        "created_at": now_str,
        "updated_at": now_str
    }
    
    try:
        # Delete existing to prevent duplication
        supabase.table("blog_posts").delete().eq("title", title).execute()
        
        # Insert
        res = supabase.table("blog_posts").insert(blog_post).execute()
        print(f"✅ Successfully seeded blog post: '{title}' into db. ID: {res.data[0]['id']}")
    except Exception as e:
        print(f"❌ Failed to seed blog post: {e}")

if __name__ == "__main__":
    asyncio.run(run_seed())
