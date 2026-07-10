# Archon 玩家旅程完整 UML 流程圖

長官，這是一份從玩家真實遊玩視角出發的**端到端 (End-to-End) 閉環流程圖**。本圖表嚴格依照 codebase 現有實體邏輯（不幻想、不預設完美路徑）繪製，涵蓋從初始動畫啟動、教學模式判斷、戰鬥 API 呼叫，直到結算存檔的完整系統互動。

> [!NOTE]
> 本流程圖採用 Mermaid 語法繪製，展示了上帝視角下的系統元件與 API 調用時序。

## 核心遊戲閉環 (Core Gameplay Loop) 時序圖

```mermaid
sequenceDiagram
    autonumber
    actor Player as 玩家 (Player)
    participant Intro as IntroVideo.tscn (OS Boot)
    participant Menu as MainMenu.tscn
    participant State as GameState.gd (Singleton)
    participant Board as GameBoard.tscn
    participant Client as BackendClient.gd
    participant API as Python FastAPI (Backend)
    participant Save as SaveManager.gd (Singleton)

    %% 啟動與選單
    Player->>Intro: 啟動遊戲 (Launch App)
    Intro->>Intro: 播放轉場動畫 (transition_os_boot.ogv)
    Intro-->>Menu: 播放完畢或點擊跳過 (Change Scene)
    
    Player->>Menu: 點擊 [New Career] 或 [Continue]
    Menu->>State: 初始化/讀取世界狀態
    Menu-->>Board: 經 TransitionVideo 載入遊戲主場景

    %% 遊戲主場景邏輯判斷
    Board->>State: 檢查教學模式 (is_tutorial_active?)
    
    alt 教學模式啟動 (Tutorial Mode)
        State-->>Board: Return True
        Board->>Client: 請求搜尋 (search)
        Client->>Client: 攔截網路請求 (Offline Fallback)
        Client->>Save: 讀取 res://assets/data/tutorial_dataset.json
        Client-->>Board: 回傳 Mock Data (無 API 呼叫)
        Board->>Player: 顯示教學引導與假想敵人
        Player->>Board: 完成教學操作
        Board->>State: 關閉教學模式 (is_tutorial_active = false)
        Board->>Save: save_progress() (寫入 user://savegame.save)
        
    else 真實戰鬥模式 (Live Combat Mode)
        State-->>Board: Return False
        Player->>Board: 執行駭客行動 / 搜尋指令 (Input Query)
        Board->>Client: 請求真實搜尋 (search)
        Client->>Save: 取得當前裝備模型 (equipped_model) 與特務權限
        
        %% 真實 API 呼叫 (帶有重試機制)
        loop 指數退避重試 (Max 3 Retries)
            Client->>API: [POST] /api/rag/hybrid-search
            Note right of Client: Payload: {query, similarity_threshold, match_count, equipped_model}
            
            alt 網路錯誤或 503 (Error >= 400)
                API-->>Client: 回傳錯誤碼
                Client->>Client: await get_tree().create_timer(1.0).timeout
            else 成功響應 (Success 200 OK)
                API-->>Client: 回傳 JSON (RAG 節點/卡牌資料)
            end
        end
        
        Client-->>Board: 發送 request_completed 信號
        Board->>Player: 算繪戰鬥結果 (Line2D, 節點資訊)
        
        %% 戰鬥結算與存檔閉環
        alt 戰鬥勝利 (Victory)
            Board->>Save: 呼叫 ProgressionSystem.award_battle_loot()
            Save->>Save: 增加 current_xp, clearance_rating
            Save->>Save: 結算掉落物 (data_core_s, player_inventory)
        else 戰鬥失敗 (Defeat)
            Board->>Save: 呼叫 ProgressionSystem.penalize_battle_loss()
            Save->>Save: 扣除 clearance_rating (Loss Penalty)
        end
        
        Save->>Save: save_progress() (寫入 user://savegame.save)
    end
    
    %% 進入後勤樞紐 (Hubs)
    Player->>Board: 點擊返回作戰中心 (Return to Hub)
    Board-->>Menu: (Change Scene)
    Player->>Menu: 進入「卡牌工坊」、「特務編制」、「駭客檔案」
    Note left of Menu: 這些場景均讀寫 SaveManager.gd 本地檔案，不呼叫 API
```

---

## 系統架構與路徑盤點 (Architecture Audit)

### 1. 唯一對外連線 API (Single Point of Truth)
目前的 Archon 數位雙生前端架構採用 **Local-First** 策略，唯一的對外連線樞紐為 `BackendClient.gd`，核心 API 如下：
*   **端點名稱**: `[POST] /api/rag/hybrid-search`
*   **觸發時機**: `GameBoard.tscn` 中的真實戰鬥階段。
*   **防禦機制**: 
    1. 具備 3 次失敗重試機制 (Retry Loop)，防禦 503 錯誤。
    2. 若遊戲位於 Web 端運行，會自動偵測 `window.location.origin` 進行動態 URL 綁定。
    3. 具備教學模式實體斷點，教學期間絕對不會向後端發送 HTTP 請求。

### 2. 存檔與狀態管理 (Progression Persistence)
*   **機制**: 遊戲的進度存檔並**未**連接至遠端資料庫 (如 Supabase)，而是 100% 透過 `SaveManager.gd` 這個 Singleton 將字典資料寫入至本地沙盒 `user://savegame.save`。
*   **閉環驗證**: 無論是戰鬥勝利的 `award_battle_loot()` 或失敗的 `penalize_battle_loss()`，最終都會呼叫 `save_manager.save_progress()`，確保玩家經驗值、卡牌庫存 (Inventory)、特務編制 (Teammates) 在應用程式重啟後依然能從初始畫面 `MainMenu` 讀取並銜接，完成完美的閉環。
