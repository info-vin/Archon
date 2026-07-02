# Phase 5.8.6: A+B+C 混合非線性 RPG 成長系統 (Non-Linear RPG Progression)

> **核心原則：深度的玩家邏輯具象化 (Player Logic Emulation)**
> 摒棄傳統打怪升級的線性思維。玩家的成長必須與 RAG 卡牌合成系統、資安階梯 (Sector Clearance)、以及對檢索邏輯的個人化微調 (Fine-tuning) 進行深度綁定。

## 1. 系統設計藍圖 (System Blueprint)

本階段將實作一套結合《皇室戰爭》與《流亡黯道》設計哲學的「三核驅動」RPG 系統。

### 1.1 A系統：經驗與合成的微小機率 (Synthesis-Driven EXP)
*   **XP 獲取**：戰鬥勝利除了給予盃數，還會發放 Account XP。
*   **認知等級 (Cognitive Level)**：XP 累積提升認知等級。等級提升不會直接增加戰鬥中的攻擊力，而是：
    1.  每升 1 級，給予 1 點 `TP (拓撲天賦點)`。
    2.  每升 1 級，被動提升卡牌工坊的基礎合成成功率 `+1%` (最高可達 20% 的微小機率加成)。

### 1.2 B系統：資安權限階梯 (Sector Clearance & Trophy Road)
用以增加玩家參與高階關卡的慾望，限制低階玩家提早接觸高等資源。
*   **CR 積分機制**：勝利增加 `Clearance Rating (CR)`，失敗扣除。
*   **階級解鎖 (Sectors)**：
    *   `Sector 1 (0-499)`：基礎毒性低，只掉落 `keyword_search` 與 B 級核心。
    *   `Sector 2 (500-999)`：毒性 20% 起跳，解鎖 `dense_search` 與 A 級核心。
    *   `Sector 3 (1000+)`：高壓防禦，解鎖 `reranker` 與 S 級核心掉落。

### 1.3 C系統：RAG 拓撲天賦星盤 (Topology Talent Web)
讓玩家模仿工程師的思考邏輯，親手改進現有的 RAG 機制。
*   **邏輯微調 (Logic Emulation)**：消耗 TP 點亮天賦樹節點，直接從底層篡改 (Fine-tune) 卡牌參數。
*   **天賦範例**：
    *   `[暴力檢索]`：所有檢索卡牌 `match_count` +3，適合喜歡高召回率的玩家。
    *   `[純粹主義]`：所有卡牌 `min_score` 閥值提高 0.1，降低假陽性，適合邏輯嚴謹的玩家。
    *   `[混合工程師]`：提早在低等級解鎖 `keyword_search` 的 `use_hybrid=true` 屬性。

---

## 2. 實作任務清單 (Implementation Tasks)

*   **[x] Task 2.1: 重構 SaveManager 與 GameState**
    *   新增 A 系統的 `cognitive_level`, `current_xp`, `topology_points`。
    *   新增 B 系統的 `clearance_rating`，並在 `start_game()` 中依據盃數動態注入關卡毒性與難度。

*   **[x] Task 2.2: 實作 C 系統的天賦微調邏輯 (Talent Modifiers)**
    *   更新 `CardData.gd` 的 `get_rag_parameters()`，使其能讀取玩家點亮的天賦節點，並動態覆寫 `match_count` 或 `min_score` 等參數。

*   **[x] Task 2.3: 整合 A 系統至 CardWorkshop**
    *   更新 `CardWorkshop.gd`，將 `cognitive_level` 帶入合成成功率的 LEAN 公式中。

*   **[x] Task 2.4: 全域常數化與硬編碼審查 (Constant Extraction)**
    *   移除所有檔案中的魔法數字與字串，將 RPG 平衡數值、階級閾值、天賦字串統一提取至各檔案頂端作為 `const`，確保企劃人員未來的可維護性。

---

> **進度更新 (2026-07-02)**：所有底層代碼（`SaveManager`, `GameState`, `CardData`, `CardWorkshop`）皆已通過實體公證與防禦性檢視，無窮迴圈與效能隱患已排除。Phase 5.8.6 邏輯層已全面結案。
