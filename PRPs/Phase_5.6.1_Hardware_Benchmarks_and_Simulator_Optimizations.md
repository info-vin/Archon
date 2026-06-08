# Phase 5.6.1: 算力基準、自動化工具硬化與 UI 治理計畫 (Hardware Benchmarks & Simulator Optimizations)

## 核心目標 (Goal)
本階段為 Phase 5.6.0 的第一部分，專注於 **建立本地/容器純 CPU 環境下的量化算力數據**、**優化百關挑戰模擬器的視覺比對與節律防禦機制**，並在 **5173 前端完成提示詞管理（Prompt Manager）的資料庫種子與介面對齊**。

---

## 建議變更與詳細實作計畫 (Proposed Changes)

### 1. 本地/容器多環境算力基準測試 (Hardware Benchmarking)
*   **目的**：消除效能上的幻想，獲取不同硬體配置與模型大小的實測推論速率。
*   **實作變更檔案**：
    *   [NEW] `scripts/benchmark_hardware.py`
*   **詳細步驟**：
    1. 撰寫基準測試腳本，自動偵測運行環境（Host macOS GPU, Host macOS CPU, Docker Container CPU）。
    2. 自動拉取或模擬不同尺寸的本地 Ollama 模型（如 `qwen2.5:0.5b`, `gemma3:1b`, `gemma3:4b`）。
    3. 量測並輸出：**模型載入冷啟動秒數**、**首字延遲 (TTFT)**、**每秒生成 Token 數 (Tokens/s)**。
    4. 將實測的能力矩陣輸出為 `.twin/diagnostics/hardware_capability_matrix.json`，作為 Phase 5.6.2 路由決策的參數基礎。

### 2. 百關模擬器視覺對帳過濾與休眠感知防禦 (Simulator Optimization)
*   **目的**：解決 simulator 執行時 VLM 呼叫資源過載的問題，降低 $P_{call}$ 觸發率。
*   **實作變更檔案**：
    *   [MODIFY] [simulator_runner.py](file:///Users/vincenta/GoogleKwok022/Archon/scripts/simulator_runner.py)
    *   [NEW] `baselines/viewport_mask.json`
*   **詳細步驟**：
    1. **動態區域遮罩 (对策 A)**：於 PIL 圖像差異比對前，讀取 `viewport_mask.json` 定義的動態 DOM 坐標（如時間戳、動態 ID），將其在對比圖中實體填充為黑色（`#000000`），降低偽隨機誤差。
    2. **限額執行模式 (对策 B)**：於 `Makefile` 與常規測試中限制 `make twin-simulator --limit 3` 以防止 CPU 過載。
    3. **休眠/斷網自動 Skip (对策 C)**：檢測 `is_hf_awake()` 狀態。若處於睡眠期或斷網環境，`vision_judge.py` 自動標記為 `[Skip VLM Judge]` 並安全返回。

### 3. Lean 4 提示詞種子資料與 5173 UI 整合
*   **目的**：提供人機協作的 Prompt 修改入口，達成 Prompt SSOT。
*   **實作變更檔案**：
    *   [11_seed_config.sql](file:///Users/vincenta/GoogleKwok022/Archon/migration/0.2.2/11_seed_config.sql) (或新增對應的 SQL patch)
    *   [init_db.py](file:///Users/vincenta/GoogleKwok022/Archon/scripts/init_db.py)
*   **詳細步驟**：
    1. 在資料庫 `prompts` 表中追加種子金鑰 `'LEAN_4_DEVELOPER_ASSISTANT'`，預設寫入 Lean 4 語法、tactics 強制約束指令及 JSON 輸出規範。
    2. 更新 `init_db.py` 確保 `make db-init` 時會自動 Append 此 Seed，並驗證其能呈現在 5173 的 Prompt Manager 管理路由頁面中。

---

## 驗證計畫 (Verification Plan)

### 1. 實證基準測試
*   執行 `python scripts/benchmark_hardware.py`，驗證其能正確產出 `hardware_capability_matrix.json`。
*   執行 `make twin-simulator --limit 3`，驗證動態遮罩與 Circadian Skip 邏輯在斷網狀態下仍能全數通過。

### 2. 自動化測試
*   驗證 `LEAN_4_DEVELOPER_ASSISTANT` 在資料庫中存在且能被後端 `prompt_service` 正確提取。
