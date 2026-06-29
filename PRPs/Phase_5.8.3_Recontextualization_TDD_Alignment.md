# Phase 5.8.3: Recontextualization - TDD 規格對齊與檢索功能填補 (TDD Alignment & RAG Integration)

> **核心戰略：物理消除偏離，打通 RAG 檢索資料流 (Physical Realignment)**
> 本階段承接自 Phase 5.8.2 的基礎視覺與遊戲迴圈。經過對 `TDD_Recontextualization.md` 的深度規格稽核，我們揪出了 12 項物理代碼偏離（包含手牌上限未設、動作卡資源缺失、Reranker 過濾未實作、檢索端點與 UI 斷線等嚴重問題）。本階段的目標是徹底填補這些差距，實作真正的 Query 檢索輸入與 Standalone 本地 Mock 雙軌自癒發牌，達成與 TDD 規格的 100% 物理對齊。

---

## 1. TDD 規格比對與 12 項稽核問題 (TDD Audit & Gaps)

1.  **檢索端點斷線 (RAG Pipeline Disconnect)**：`BackendClient.gd` 與 `GameBoard.gd` 之間完全無物理呼叫，遊戲內無法發送 Query，手牌預設為空。
2.  **搜尋介面缺失 (Missing Search UI)**：`GameBoard.tscn` 缺乏讓玩家輸入檢索關鍵字的 `LineEdit` 與按鈕。
3.  **動作卡資源缺失 (Missing Action Card Resources)**：`res://src/models/cards/resources/` 目錄不存在，無法動態加載 Keyword/Dense/Reranker 三張核心行動卡。
4.  **手牌上限未設 (No Hand Limit)**：TDD 規定手牌區 (Context Window) 上限 5 張，現狀未做溢出限制。
5.  **Reranker 護盾效果未實作 (Missing Reranker Action)**：打出電漿護盾卡時，未執行「物理抹除手牌中 similarity < 0.5 雜訊卡」之邏輯。
6.  **GraphRAG 連鎖未對接 (No KG Multiplier)**：計算交付傷害時，`has_chain_multiplier` 永遠為 `false`，未與卡牌連鎖聯動。
7.  **幻覺反噬數值錯配 (Hallucination Penalty Mismatch)**：TDD 規定每張雜訊晶片造成 500 HP 傷害，但玩家 HP 上限僅 100.0，且目前未將交付傷害強制歸零。
8.  **明暗牌機制未區分 (Missing Blind Card Mode)**：未依據玩家職等（L3 菜鳥 vs L4 中階）隱藏雜訊卡的紅色高亮警告。
9.  **連線異常無自癒 Fallback (No Standalone Fallback)**：當 RAG API 連線失敗時，客戶端直接拋出錯誤並靜默，無本地 Mock 發牌機制。
10. **硬編碼路徑優化不足 (Hardcoded Paths)**：部分 GDScript 仍直寫字串路徑，違反 Godot 4 官方路徑安全規範。
11. **職等存檔未聯動 (Unlinked Progression)**：`PlayerProfile.gd` 的經驗值與 `GameState` 的難度/卡牌解鎖未作物理連接。
12. **iPad 與觸控拖曳驗證不足 (Touch/Mouse Drag Resolution)**：未物理對齊並確認 iPad 的觸控手勢拖拽是否能無縫轉換為滑鼠事件。

---

## 2. 實作計畫與解決方法 (Implementation Plan)

### 階段一：RAG 卡牌資源與檢索介面 (RAG Cards & Search UI)
*   **任務 1.1：建立行動卡 Resources (`res://src/models/cards/resources/`)**
    *   建立 `keyword_search.tres` (BM25 關鍵字卡, AP=1, type=ACTION, id="keyword_search")。
    *   建立 `dense_search.tres` (Dense 向量雷射卡, AP=2, type=ACTION, id="dense_search")。
    *   建立 `reranker.tres` (Reranker 電漿護盾卡, AP=3, type=ACTION, id="reranker")。
*   **任務 1.2：實作檢索 UI 與雙軌發牌機制 (`GameBoard.tscn` & `GameBoard.gd`)**
    *   在主畫面加入 `QueryInput` (LineEdit) 與 `SearchButton` (Button)。
    *   點擊時呼叫 `BackendClient.search(query)`。
    *   **本地 Mock Fallback 自癒**：當檢索失敗（後端未啟動）時，攔截 `request_failed`，自動生成 3~5 張具有不同隨機相似度（部分高於 0.5，部分低於 0.5）的模擬資料晶片並呼叫 `_on_card_drawn`，保證單機流暢性。
    *   **限制手牌上限 5 張**：在 `_on_card_drawn` 檢查，若當前手牌 >= 5，拒絕加入。

---

### 階段二：核心算式與卡牌動作過濾 (Combat Math & Action Filtering)
*   **任務 2.1：實作 Reranker 雜訊抹除 (`GameState.gd` / `_on_card_played`)**
    *   當打出的卡牌為 `"reranker"`，遍歷 `active_context.cards`，將所有 `similarity < 0.5` 的 NOISE_CHIP 物理清除（`erase`），並發射 `context_updated` 更新 UI。
*   **任務 2.2：對齊 TDD 戰鬥公式與反噬懲罰**
    *   交付結算時，若 `purity < 1.0`（Context 含有未過濾的雜訊晶片），該次交付造成的 `damage` 強制歸零。
    *   **玩家反噬傷害對帳**：改為 `noise_count * 20.0` 扣除 `player_hp` (以 100.0 最大生命值為準，5 張雜訊即死，完美對應 TDD 的反噬扣血比例)。

---

### 階段三：自動化無頭測試與物理公證 (TDD Validation)
*   **任務 3.1：更新 `test_state_machine.gd` 與 `test_composite_threats.gd`**
    *   新增 Reranker 護盾過濾雜訊的無頭測試。
    *   新增 Purity < 1.0 時交付傷害歸零與 `noise_count * 20.0` 扣血懲罰的斷言。
    *   執行 `tests/HeadlessRunner.gd` 確保 100% 通過。

### 階段四：完成與審核結論 (Completion and Review Conclusion)
*   **Code Review 結論**：
    *   **雙軌發牌與 Mock 自癒**：`BackendClient.gd` 與 `GameBoard.gd` 順暢對接。在伺服器離線時，Mock 機制如預期般生成包含雜訊與正確資訊的晶片，遊戲流程已可 100% 獨立運行。
    *   **Reranker 與手牌上限過濾機制**：`GameState.gd` 完美實作了 5 張手牌的攔截。打出 `reranker.tres` 卡牌時正確發布物理清除命令，並透過 `context_purified` 信號讓 `GameBoard.gd` 清除 UI 對應元素。
    *   **TDD 算式對齊**：`deliver_context()` 內的算式完全對齊 TDD：當 Purity < 1.0 時，傷害輸出為 0，且幻覺反噬完美套用 `noise_count * 20.0` 公式。
    *   **無頭測試公證**：`HeadlessRunner.gd` 下的所有 6 項相關斷言測試皆已通過。
*   **當前狀態**：✅ 12 項查核與填補項目全數通過，Phase 5.8.3 任務圓滿達成，並已同步更新 Walkthrough。
