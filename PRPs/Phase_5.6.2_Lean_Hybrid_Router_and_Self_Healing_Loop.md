# Phase 5.6.2: Lean 4 混合路由器、編譯驗證器與協同自癒閉環計畫 (Lean 4 Hybrid Router & Self-Healing Loop)

## 核心目標 (Goal)
本階段為 Phase 5.6.0 的第二部分，專注於 **實作後端 Lean 4 實體專案編譯與錯誤解析封裝**、**建立基於 AST 複雜度與期望值評估的混合推理路由器**，以及 **打造本地與雲端雙端協同自癒與 code_examples 知識庫沉澱閉環**。

---

## 建議變更與詳細實作計畫 (Proposed Changes)

### 1. Lean 4 本地編譯驗證器 (Lean 4 Compiler Wrapper)
*   **目的**：讓後端具備物理編譯 Lean 4 專案並解析語法/邏輯錯誤的能力。
*   **實作變更檔案**：
    *   [NEW] `python/src/server/services/lean/compiler_service.py`
*   **詳細步驟**：
    1. 實作 `LeanCompilerService` 類別，透過 `subprocess` 安全調用位於 `lean_proofs/` 的 `lake build` 指令。
    2. 撰寫 `parse_lake_errors(stdout: str) -> dict` 解析器，將編譯出錯的代碼行數、tactic 失敗原因轉化為結構化的錯誤 JSON。

### 2. 混合推理路由器 (Hybrid Reasoning Router) 實作
*   **目的**：依據實測算力數據與證明難度，動態決定將任務留在本地（Tier 3）還是外包雲端（Tier 1）。
*   **實作變更檔案**：
    *   [NEW] `python/src/server/services/llm/hybrid_router.py`
    *   [MODIFY] [base.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/llm/base.py)
*   **詳細步驟**：
    1. 實作 `HybridRouter`，載入 Phase 5.6.1 產出的 `hardware_capability_matrix.json` 算力數據。
    2. 實作 `evaluate_complexity(proof_context: str) -> int` 函式，解析當前 Lean 證明的目標假設與 AST 節點大小（大於閾值 $S \approx 150$ 則外包）。
    3. 在 `base.py` 路由入口注入 `HybridRouter`。若複雜度過高或本地重試次數 $K \ge 2$，自動外包至雲端 Pro 模型，否則派發給本地 Ollama。

### 3. 雙端協同自癒與知識沉澱進化閉環 (Two-Stage Repair & Seeding)
*   **目的**：實現「雲端一次自癒，本地永久學習」的自適應進化閉環。
*   **實作變更檔案**：
    *   [NEW] `python/src/server/services/lean/self_healing_service.py`
    *   [MODIFY] [knowledge_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/knowledge/knowledge_service.py) (或 RAG 向量寫入端點)
*   **詳細步驟**：
    1. **二階段自癒迴圈 (Two-stage Repair Loop)**：
       * **本地自癒 (Stage 1)**：本地編譯失敗時，以 `compiler_service` 的錯誤 JSON 為 Context，結合 `LEAN_4_DEVELOPER_ASSISTANT` 提示詞，讓本地 Ollama 於沙盒內進行語法與 minor bugs 自我修正。
       * **雲端升級自癒 (Stage 2)**：若本地嘗試 $K$ 次仍未通過，打包「嘗試歷史與編譯反饋」，升級發送至雲端 Pro 模型進行高精度修復。
    2. **自適應進化沉澱 (Evolutionary Knowledge Seeding)**：
       * 雲端修復成功的 Lean 4 證明程式碼，自動被轉化為向量 Embedding，存入資料庫的 `code_examples` 知識庫中。
       * 下次本地執行類似的定理證明時，RAG 將自動檢索此案例作為 few-shot 範例餵給本地 Ollama，達成自我進化。

---

## 驗證計畫 (Verification Plan)

### 1. 自動化測試
*   新增測試驗證 `compiler_service.py` 能正確捕獲並解析 `lake build` 的錯誤輸出。
*   新增測試驗證 `HybridRouter` 能依據 AST 節點大小與 K 次限制，精準切換 Tier 1 與 Tier 3 分支。
*   驗證修復成功後，`code_examples` 的向量寫入邏輯正常，且本地 RAG 能成功檢索到該案例。

---

## 實作結果與現狀 (Implementation Results - Status: Completed)

所有任務已於 2026/06/08 順利完成：
1. **Lean 4 編譯器封裝完成**：新增了 `LeanCompilerService`，能調用 `lake build` 並精確解析錯誤。
2. **混合推理路由器落地**：新增 `HybridRouter` 並在 `base.py` 路由入口注入。可自動依據 AST 複雜度及重試次數進行本地與雲端的分流。
3. **二階段自癒與數據沉澱閉環**：新增 `LeanSelfHealingService` 串接兩階段自癒。編譯成功後的證明程式碼會自動寫入 `code_examples` 以便日後 RAG 檢索。
4. **單元測試全數通過**：通過 `test_lean_compiler.py` 與 `test_hybrid_router.py`，全數綠燈。
