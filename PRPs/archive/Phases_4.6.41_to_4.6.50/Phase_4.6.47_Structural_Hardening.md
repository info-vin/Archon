# Phase 4.6.47: 結構物理加固與數據對帳計畫 (Structural Hardening & Data Parity)

## 1. 現狀數據診斷 (Status Quo - Data Backed)
根據 2026-04-29 的物理審計，系統存在以下斷層：
*   **PRP 缺失**：4.6.47 計畫未物理成案，導致執行路徑混亂。
*   **數據語法錯誤 (22P02)**：`ai-market-bot` 非 UUID 格式，導致 Bob (Marketing) API 報 500 錯誤。
*   **大型檔案堆積**：4 個核心模組超過 500 行 SOP 警戒線（最高 619 行）。
*   **測試神經脆弱**：之前的瘦身重構未考慮 pytest 的物理 Patch 路徑，導致大量 AttributeError。

## 2. 核心執行目標 (Objectives)
*   **[目標 A] 物理成案**：完成此 PRP 文件並作為執行 SSOT。
*   **[目標 B] 恢復 Bob 工作流**：修正 UUID 語法錯誤，使 `make persona-audit` 達到 5/5 綠燈。
*   **[目標 C] 負責任瘦身**：將 4 個巨型檔案降至 500 行以下，且 **不准噴出任何 AttributeError**。
*   **[目標 D] 穩定性對帳**：確保 `make test-be` 維持在 559/559 Passed 基準線。

## 3. 實體執行路徑 (Action Plan)

### 第一階段：修復數據死穴 (Immediate Fixes)
1.  **UUID 歸一化**：修改 `shared_constants.py` 或 `agent_registry`，將 `ai-market-bot` 物理對應為合法的 UUID，消除 22P02 錯誤。
2.  **Alice 視野同步**：確保 `MarketingService.list_leads` 包含 `or_.is.null` 過濾。

### 第二階段：結構化減重 (Modularization without Breakage)
1.  **MarketingService 拆分**：將 Stats 邏輯物理遷移至子模組，並在頂層匯出所有被 Patch 的屬性。
2.  **RAGService 拆分**：將 Web Research 物理遷移至子模組，保留 `genai` 匯出供測試 Patch。
3.  **ThreadingService 拆分**：將流量控制邏輯遷移至 `utils/rate_limiter.py`。
4.  **CredentialManager 拆分**：遷移 Provider Discovery，但保留 Row-based Cache 結構。

### 第三階段：物理公證 (Final Verification)
1.  執行 `make lint` 確保無 E701 單行語法錯誤。
2.  執行 `make persona-audit` 確保 5/5 OK。
3.  執行 `make test-be` 確保 559/559 Passed。

## 4. 驗收數據指標 (Success Metrics)
*   `archon-server` 容器狀態：**Healthy**
*   巨型檔案行數：**全部 < 500 LOC**
*   Error Code 掃描：**0 筆 22P02, 0 筆 404/500**
*   Persona Audit：**5/5 Success (200)**
