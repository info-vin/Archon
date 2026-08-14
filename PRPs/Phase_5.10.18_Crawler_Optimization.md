# [Phase 5.10.18] Crawler Optimization & Loop Remediation

您的直覺與考量完全正確！**把淘汰的垃圾資料寫進資料庫確實很不合理，不僅造成髒資料，還增加了維護成本。**
我們根本不需要大改架構（不需要解耦寫入資料庫），因為真正的效能兇手，是代碼裡隱藏的「無效 LLM 呼叫」。
按照您的指示，我繪製了新舊流程的 UML 對比圖（包含 DAG 排程事件流），並加入了絕對嚴格的自動化驗證計畫。

## 流程對比與 DAG 事件流 (UML Sequence Diagram)

> **回答您的提問：** 是的！修改後完全保留了原有的精準漏斗防線：`RAG分數 (與 HyDE 比較) -> LLM Judge (Y/N) -> Infer Need`。我們只是把原本「偷跑」在第一關之前的 `infer_need`，移回了漏斗的最後一關。

```mermaid
sequenceDiagram
    participant S as Scheduler (DAG Engine)
    participant C as Crawler Service
    participant AI as Evaluator (Gemini)
    participant DB as Supabase
    
    rect rgb(255, 230, 230)
        Note over S, DB: 【目前錯誤流程】 無差別 LLM 呼叫與限流地獄
        S->>C: start auto_fetch_daily_leads (DAG Step 1)
        loop For Page 1 to max_pages
            loop For Keyword in Keywords
                C->>C: fetch 32 jobs from 104
                C->>AI: ❌ 暴衝：對所有 32 筆執行 infer_need()
                AI-->>C: 🚨 卡死 5~8 分鐘 (觸發 15 RPM 限流)
                C->>DB: 查詢已存在的 URL
                C->>AI: 防線 1: RAG 分數 (與 HyDE 比較)
                C->>AI: 防線 2: llm_judge (Y/N)
                C->>DB: Insert 最終通過的名單
            end
            Note over C: ❌ 檢查 total_new_leads > 0 (太晚了！)
        end
        S-->>S: 排程超時 (耗費 40+ 分鐘)
        S-xS: ❌ 導致下游 DAG 報告任務 (Bob/Nexus) 被阻塞或直接中斷！
    end

    rect rgb(230, 255, 230)
        Note over S, DB: 【修改後流程】 延遲取值與正確的迴圈優先權
        S->>C: start auto_fetch_daily_leads (DAG Step 1)
        loop For Keyword in Keywords
            loop For Page 1 to max_pages
                C->>C: fetch 32 jobs from 104
                Note over C: ✅ 拔除提前的 LLM 呼叫！
                C->>DB: 查詢已存在的 URL
                C->>AI: 防線 1: RAG 分數 (與 HyDE 比較)
                Note over AI: 漏斗過濾：剩下約 5 筆
                C->>AI: 防線 2: llm_judge (Y/N)
                Note over AI: 漏斗過濾：剩下約 2 筆
                C->>AI: ✅ 防線 3: 僅對最後 2 筆執行 infer_need()
                C->>DB: Insert 最終通過的名單
                Note over C: ✅ 若名單 > 0，立刻 break 翻頁，換下個關鍵字！
            end
        end
        C-->>S: Return 成功 (耗費不到 2 分鐘)
        S->>S: ✅ 發送 DAG Event (CRAWLER_SUCCESS)
        S->>DB: 順暢觸發下游 Report Tasks
    end
```

## 具體修改計畫 (Proposed Changes)

### [NEW] `@PRPs/Phase_5.10.18_Crawler_Optimization.md`
- 將本計畫存檔，作為歷史稽核與防堵虛假開發的實體依據。

### [MODIFY] `python/src/server/services/job_board_service.py`
1. **消除提前的 LLM 呼叫 (Lazy Evaluation)**：
   - 刪除 `search_jobs` 方法中 `needs = await asyncio.gather(...)` 的邏輯。
   - 讓 `JobData` 保持原始狀態，推遲到 `identify_leads_and_save` 的漏斗最後一關（通過向量與 Judge 之後）才呼叫 `infer_need`。
2. **修正翻頁迴圈位置**：
   - 將原本的 `page` 迴圈移到 `keyword` 迴圈內部。
   - 當某個 `keyword` 的當前頁面有抓到新資料寫入 (`total_new_leads > 0`)，立刻 `break` 結束這個關鍵字的翻頁，進行下一個 `keyword`。

### [MODIFY] `python/tests/server/services/test_job_board_service.py`
- 修改 `test_auto_fetch_pagination_fallback`，確保測試涵蓋了正確的迴圈邏輯（Mock 行為必須精準反射 `keyword` 外層、`page` 內層的行為），並斷言 `search_jobs` 不會再偷跑 LLM 呼叫。

## 嚴格自動化驗證 (Hard Verification Plan)

為了杜絕虛假驗證，我將新增並執行 `scratch/verify_5.10.18.py`，該腳本會執行實體代碼掃描與測試斷言：
1. **代碼實體掃描 (AST/Grep)**：
   - 斷言 `job_board_service.py` 的 `search_jobs` 函數中，**絕對不存在** `evaluator.infer_need` 的字眼。
   - 斷言 `auto_fetch_daily_leads` 函數中，`for keyword in keywords:` 出現在 `for page in range(1, max_pages + 1):` 的**外層**。
2. **單元測試公證**：
   - 腳本將自動呼叫 `uv run pytest tests/server/services/test_job_board_service.py -v`。
   - 只有當以上物理條件與測試 100% 亮綠燈時，才允許進行 git commit，徹底封殺樂觀路徑。
