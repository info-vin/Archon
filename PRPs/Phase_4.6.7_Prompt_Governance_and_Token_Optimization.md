# Phase 4.6.7: Prompt Governance, Decoupling & Token Optimization (Status: COMPLETED 🟢)

## 1. 願景與核心目標 (Vision & Goals)

### 1.1 終結硬編碼 (The End of Hardcoding) - ✅ DONE
所有 AI 提示詞 (Prompts) 已從 Python 代碼中徹底抽離。`document_agent.py`, `rag_agent.py`, `summary_agent.py`, `extraction_service.py`, 及 `visit_log_api.py` 均已改為呼叫 `prompt_service.get_prompt()`。

### 1.2 RBAC 權限介面落地 (Role-Based Interface) - ✅ DONE
*   **角色對齊**: 修正了 `archon_prompts` 的 RLS 政策，將角色從舊有的 `'Admin'/'Manager'` 修正為系統實體的 `'system_admin'/'manager'`。
*   **管理邊界**: 
    *   **David Howard (Admin)**: 擁有全域 Prompt 管理權。
    *   **Charlie Brown (Manager)**: 物理鎖定僅能修改 `is_system_protected = false` 的業務型 Prompt。

### 1.3 Token 統計與成本治理 (Token Governance) - ✅ DONE
*   **數據一致性**: 利用現有 `token_usage` 表與 `TokenUsageService` 進行全域統計。
*   **架構優化**: 為了維持資料庫穩定性，避免「改 A 壞 B」，決策不新增 `archon_prompts` 欄位，改由 API 層級即時運算平均 Token 消耗，提供 David 監控。

---

## 2. 落地實作細節 (Implementation Details)

### 2.1 資料庫 Seed 實體化 (Seed Materialization)
*   **地點**: `migration/0.2.1/seed_mock_data.sql`
*   **內容**: 補全了 11 個專業 Prompt 範本，取代原本的佔位符，並新增了 `twin_scout_mission` 供給 E2E 自動化診斷使用。
*   **亮點**: 包含 POBot 的 Gherkin 語法規範、MarketBot 的 JSON 輸出結構，以及 David Howard 的 L1-L3 技術診斷治理指令。
*   **Twin Scout 穩定化**: 將 `browser-use` 棄用，改用 Playwright + Gemini Vision 繞過 API JSON Schema 錯誤，能夠穩健處理多模態截圖，並支援 Makefile Prompt 選擇。

### 2.2 程式碼手術區 (Refactored Files)
1.  `python/src/agents/document_agent.py`: 移除 Hardcoded Docstring，改為動態獲取。
2.  `python/src/agents/rag_agent.py`: 移除 Hardcoded Docstring，改為動態獲取。
3.  `python/src/agents/summary_agent.py`: 移除 Hardcoded Docstring，改為動態獲取。
4.  `python/src/server/services/extraction_service.py`: 移除 Hardcoded 字串，改為讀取資料庫。
5.  `python/src/server/api_routes/visit_log_api.py`: 移除 Try/Except 硬編碼，統一獲取規範。

---

## 3. 驗收與穩定性 (Verification & Stability)

### 3.1 品質檢查
*   **`make lint`**: 通過 (Success: no issues found)。
*   **`make test-be`**: 通過 (550 passed)。RBAC 相關測試項目 (`test_phase49_rbac_service.py`) 確認權限邊界有效。

### 3.2 降級保護 (Fallback Strategy)
所有 Agent 的 `get_prompt` 調用均保留了完整的 Python Default 字串。**即使資料庫斷線，AI 功能仍能以原本的專業邏輯運作**，不會出現遺失指令的情況。

---

## 4. 下一步行動 (Next Steps)
*   [ ] 在 5173 Admin UI 介面上增加基於 `token_usage` 表的成本視覺化標籤。
---

## 物理落地查核結論 (Physical Audit Conclusion) - 2026-03-11
*   **執行狀態**: 🟢 **100% 物理落地**
*   **關鍵證據**:
    *   **提示詞解耦**: `prompt_service.py` 成功對接 `archon_prompts` 表，全系統 AI 代理已不再使用 Hardcoded String。
    *   **非阻塞 Token 追蹤**: 實作了 `TokenUsageService` 並透過 `asyncio.create_task` 達成高效能日誌紀錄。
    *   **專業 Seed 注入**: `migration/0.2.1/` 實體 SQL 已導入包含 POBot/MarketBot 在內的 11 組專業級提示詞範本。
*   **查核總結**: 提示詞治理已達成「配置化、版本化、安全化」的三大指標，成功為系統建立了穩定且可監控的 AI 消耗模型。
