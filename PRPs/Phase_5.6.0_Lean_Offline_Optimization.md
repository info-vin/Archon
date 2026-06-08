# Phase 5.6.0: Lean 整合、離線與自動化工作流優化計畫 (Lean & Offline Workflow Optimization)

## 核心目標 (Goal)
本階段目標在於銜接已完成的 Phase 5.5 系列成果，針對 **Lean 4 本地/雲端輔助證明**、**本地算力效益匹配**，以及 **Digital Twin 百關模擬器的運行負擔與視覺對帳** 進行整合性優化與文件化。

---

## 研發背景與實證假設 (Hypothesis & Objectives)

> [!WARNING]
> **假設防禦與數據補強**：本計畫所提之三項優化對策，目前皆為「工程實證假設 (Hypotheses)」。本階段的第一步任務**必須是收集有效數據與執行基準測試 (Benchmarking)**，以驗證本地 VLM 在不同硬體加速（CPU vs Metal/GPU）下的效能落差，避免盲目樂觀開發。

### 1. 痛點一：本地模型算力與 Docker 啟動效益比值失衡
*   **現狀與瓶頸**：Docker 啟動僅需 15~30 秒，但若將 Ollama 服務直接執行於 Docker 容器內，由於無法共享 macOS Host 的 Metal (GPU) 硬體加速，模型推理會降階為純 CPU 運算。此時推理 `gemma3:4b` 速度將降至 2~5 tokens/s，導致運算時間過長，失去離線開發之意義。
*   **實證對策**：
    *   強制實施 **「Host-Bridged Ollama」架構**：Ollama 執行於宿主機 (Host macOS) 以獲取 Metal GPU 加速（推論速度 > 30 tokens/s），Docker 內部的 Agent/後端服務則透過網域 `http://host.docker.internal:11434` 進行回環呼叫。
    *   **基準數據測試指標**：記錄 Host GPU 模式 vs Docker CPU 模式的載入秒數與推論 Token 速率，做成 Parity 報告。

### 2. 痛點二：兩種 LLM 推理深度與編譯等待時間匹配
*   **現狀與瓶頸**：本地 3B~4B 級別模型（如 `gemma3`）並不具備高難度的定理邏輯推導與 Proof Search 能力。若讓其嘗試編寫複雜的 Lean 4 證明，將因語法錯誤被 `lake build` 不斷退件，陷入無意義的 CPU 運算迴圈。
*   **實證對策**：
    *   **混合推理路由 (Hybrid Reasoning Router)**：
        *   **本地模型**：僅用於 Lean 4 代碼語法自動補全、結構樣板生成 (Boilerplate) 及基礎 Induction 架構。
        *   **雲端 Pro 模型 (Tier 1)**：涉及嚴格的邏輯定理搜索時，直接路由給雲端 Gemini，不佔用本地 CPU 時間。

### 3. 痛點三：百關挑戰（Digital Twin Simulator）與工作流自動化驗證的運行負擔
*   **現狀與瓶頸**：`simulator_runner.py` 執行 E2E 併發測試時，若因動態欄位或網絡混沌注入導致像素差異大於 5.0%，會觸發 `vision_judge.py`（多模態 VLM 判定）。在本地執行時，高頻呼叫 VLM 會給 CPU 帶來極大壓力，導致百關挑戰執行超時。
*   **實證對策**：
    *   **對策 A：動態 DOM 遮罩過濾 (Dynamic Masking)**：在 PIL 像素比對階段，使用 Mask 主動排除「時間戳記」、「Log 內容」與「變動計數器」等動態區域，使靜態版面的對比準確率提升，將模型呼叫次數降至最低。
    *   **對策 B：限額防禦模式 (Limit Mode)**：Makefile 常規測試僅限額跑 `--limit 3` 關卡，Major Release 整合測試才跑 100 關。
    *   **對策 C：網路與睡眠感知 (Circadian Skip)**：當 HF 處於休眠期（台灣時間 00:18 ~ 06:41 CST）或本機斷網時，對策二（VLM 評判）自動降階為 `[Skip VLM Judge]`，以防 CI/CD 因連線崩潰。

---

## 建議變更 (Proposed Changes)

### 1. 資料庫 Prompt 治理整合 (Prompt Seeding & UI Sync)
*   **資料庫種子**：在 `prompts` 表中注入 `LEAN_4_DEVELOPER_ASSISTANT`，預設寫入 Lean 4 的基礎語法、Tactics（如 `intro`, `rfl`, `simp`）與 JSON 輸出格式約束。
*   **UI 串接**：確保該 Key 於 5173 的 Prompt Manager 中能被讀取、修改與儲存，實現人機協作控制。

### 2. Hugging Face Serverless Fallback 架構優化
*   **中繼層 (Tier 2) 評估**：
    *   **運算資源**：使用免費的 HF Serverless Inference API 執行開源輕量模型（如 `Qwen/Qwen2.5-7B-Instruct`），不吃本機 CPU/記憶體。
    *   **侷限性容災**：
        *   **429 速率限制**：當 HF 發生 Too Many Requests 時，自動滑順降階至 Tier 3 (本地 Ollama)。
        *   **冷啟動 (Cold Start)**：加入 10~30 秒的超時自癒與前端動態狀態指示，優化開發體驗。

---

## 驗證計畫 (Verification Plan)

### 1. 實證基準測試 (Empirical Benchmarks)
*   執行本地 native Ollama 在開啟/關閉 Metal 加速下的運算比對，確保推論延遲小於 10s。
*   驗證 `make twin-simulator --limit 3` 於離線環境下，PIL 對比與 `vision_judge` 降階機制運作正常。

### 2. 自動化測試
*   新增測試確保 `LEAN_4_DEVELOPER_ASSISTANT` Prompt 能被後端正確載入，且在 DB 斷線時能正確回退至代碼中的 default prompt。
