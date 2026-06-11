# Archon Spin-off: Game Concept Document

## 專案概述 (Project Overview)
本文件記錄了基於 Archon 專案（人機協作工作流）所衍生的 Godot 遊戲概念提案。
目的在於將嚴肅的企業級工作流轉化為具有趣味性的遊戲機制，藉此展現 AutoGen 與多代理人 (Multi-Agent) 協作的核心精神。

---

## 提案 1：【Archon: Token 塔防】(Token Tower Defense)
**核心理念**：將處理客戶需求與 Bug 視覺化為塔防遊戲，最能體現 AutoGen 中資源分配與 Agent 專長的差異。

*   **核心玩法**：玩家扮演「Manager (Charlie)」，要在一波波的「客戶需求 (Bug / Leads)」攻擊下守住公司。
*   **遊戲機制**：
    *   **敵人 (Enemies)**：不斷湧入的未處理工單 (Tickets)、客訴、行銷危機。
    *   **防禦塔 (Towers)**：玩家佈署的 AI Agents (DevBot, MarketBot, POBot)。
    *   **資源 (Resource)**：**Token 預算 (Token Budget)**。佈署 Agent 與發射攻擊皆會消耗 Token。
    *   **攻擊方式 (Prompting)**：Agent 塔發射的不是子彈，而是「Prompt (提示詞)」。
    *   **屬性相剋**：不同 Agent 擅長處理不同的敵人。將技術 Bug 交給 MarketBot 處理會造成「Token 浪費」且效率低下。
    *   **星環協作 (Star Topology)**：面對大型 Boss（跨部門需求），玩家必須在多個 Agent 之間手動建立通訊連線。討論過程中會噴出對話泡泡（具象化預算熔斷與多輪對話機制）。
    *   **失敗條件**：Token 預算耗盡，或未處理的工單壓垮伺服器防線。

---

## 提案 2：【Archon: 公司模擬器】(Agency Tycoon)
**核心理念**：採用 2D 橫向剖面視角（類似《Fallout Shelter》），將團隊管理與 AI 基礎設施具象化。

*   **核心玩法**：放置型/資源管理模擬經營遊戲。
*   **遊戲機制**：
    *   **場景設計**：畫面是公司的切面，劃分為不同部門房間 (Sales, Marketing, Engineering)。
    *   **角色互動**：房間內有人類員工 (Alice, Bob) 以及代表 Agent 的伺服器機櫃。玩家點擊派發任務後，可看見人類員工走到伺服器前「喚醒」對應的 Agent。
    *   **實體化除錯 (Chaos Events)**：系統會隨機發生真實專案中的痛點事件。例如發生「RAG 假陽性」或「API 503 限流」時，部門房間會閃爍紅燈甚至起火，玩家必須及時派出 DevBot (小機器人) 進行修復滅火。
    *   **成長系統 (Upgrades)**：隨著遊戲推進，玩家可賺取資金解鎖更高等級的 Prompt，或是將 Local 模型升級（從 Ollama 1B 升級至 4B），以提升處理速度與容錯率。

---

## 提案 3：【Archon: RAG 潛入駭客】(Semantic Infiltration)
**核心理念**：將「向量資料庫檢索 (RAG)」過程設計為迷宮潛行遊戲，具象化資料檢索的困難與機制。

*   **核心玩法**：上帝視角的 2D 潛行解謎遊戲。
*   **遊戲機制**：
    *   **主角與場景**：玩家控制一台名為 `Query` 的小飛船，在名為 `Knowledge Base` 的向量網格迷宮中穿梭。
    *   **任務目標**：在複雜的網格中找到最閃亮的核心水晶 (`Target Chunk`) 並將其運送至終點 (LLM)。
    *   **干擾與敵人**：迷宮中遊蕩著名為 `Semantic False Positive (語意假陽性)` 的怪物。若飛船碰到它們，將會攜帶「被污染的 Context」至終點，導致 LLM 生成幻覺，遊戲失敗。
    *   **防禦機制**：玩家可消耗能量開啟 `Similarity Threshold (相似度閾值)` 護盾，用於彈開或過濾假陽性怪物（對應 Phase 5.6.5 的數學證明與邊界限縮）。

---

## 數據化難度分析與 Lean 決策 (Data-Driven Complexity & Lean Decision)

為確保開發符合 Lean (精實開發) 之 MVP 精神，我們針對 Godot 4.x 引擎底層的「節點複雜度 (Node Complexity)」、「物理運算 (Physics)」、「狀態機複雜度 (FSM)」與「UI 耦合度」進行了量化評估：

### 量化分析矩陣

| 評估維度 | 提案 1 (塔防) | 提案 2 (公司模擬) | 提案 3 (潛入駭客) |
| :--- | :--- | :--- | :--- |
| **物理碰撞依賴** | 中 (`Area2D` 偵測) | 低 | **高** (`CharacterBody2D` 滑動) |
| **動態尋路依賴** | **極低 (沿 `Path2D` 走)** | 低 (`Tween` 直線) | **高 (`NavigationAgent2D`)** |
| **狀態機複雜度** | 中 | **極高** (排程與等待死鎖) | 中高 (巡邏與追跡) |
| **UI 開發成本** | 中 | **極高** (重度依賴 `Control`) | 低 |
| **MVP 最小工時** | **最少 (3-5天)** | 最多 (7-10天) | 中等 (5-7天) |

### 🏆 決策結論：選擇【提案 1 - Token 塔防】

基於量化數據與 Lean 原則，**提案 1** 為阻力最小、風險最低的開發路徑，其核心優勢包含：
1. **消除浪費 (Eliminate Waste)**: 塔防遊戲完全不依賴高風險的動態導航網格 (NavMesh)，敵人依循固定的 `Path2D` 貝茲曲線移動，大幅削減開發與除錯時間。
2. **狀態機單純 (Reduce State Space)**: 實體的狀態流轉（射擊、移動、消滅）簡單明確，沒有提案 2 中複雜的時序依賴與死鎖 (Deadlock) 風險。
3. **快速驗證 (Build-Measure-Learn)**: 核心循環 (佈署 Agent -> 消耗 Token -> 消滅 Bug) 能夠極快地透過幾何佔位符 (Placeholder) 實作並進行遊玩測試，確保遊戲性。

---

## 結語與下一步 (Next Steps)
本文件僅作為概念發想 (Pitch Deck) 使用。
若決定正式啟動開發，需從上述提案中擇一，並進一步撰寫詳細的 **GDD (Game Design Document)** 以定義 Godot 節點結構、美術風格與數值平衡。