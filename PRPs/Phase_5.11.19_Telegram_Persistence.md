# Phase 5.11.19: Telegram 持久化佇列 (雲端關機盲區防禦)

## 📌 背景與物理真相 (Context & Physical Truth)
過去針對 Telegram 連線逾時的修復 (Phase 5.11.11, 5.11.13) 皆落入「樂觀路徑」與「單機思維」，企圖使用 `httpx` 逾時延長與 `asyncio.sleep()` 來硬抗網路斷層。
經由 09-19 日誌實體驗證，發現：
1. **關機盲區 (Shutdown Blindspot)**：報告產出時間 (16:18 CST) 處於機器逼近休眠且無外部 HTTP 流量的時刻，網路瞬斷時間長達 **84 秒以上**。
2. **排隊關機 (Volatile Memory Death)**：在 Serverless (Hugging Face) 環境中，若使用記憶體層級的背景佇列 (Background Tasks / sleep) 進行重試，一旦容器進入休眠，記憶體即被抹除，導致通知永久遺失。

## 🎯 目標 (Objectives)
徹底拋棄網路層的硬幹與幻想。將「發送失敗的通知」視為一種「系統任務」，將其持久化至資料庫 (`archon_tasks`)。當系統下一次被喚醒且網路健康時，再由排程器將其補發，達成 100% 存活率。

## 🛠️ 實作計畫 (Implementation Plan)

### 1. `telegram_service.py` (降級為持久化任務)
*   **攔截失敗**：在 `send_message` 經歷 3 次重試失敗後，不再只是寫入 `archon_logs`。
*   **任務化 (Taskification)**：將未送出的訊息內容包裝，透過 `BaseRepository` 寫入 `archon_tasks`。
    *   `title`: `"[System] Pending Telegram Alert"`
    *   `description`: `<Telegram 訊息本文>`
    *   `status`: `"todo"`
    *   `assignee_id`: `"system"` (或保留為 null)

### 2. `task_dispatcher.py` (健康狀態下的補發機制)
*   **佇列消化 (Queue Flush)**：在 `task_dispatcher.py` 定期執行時 (每 3 分鐘)，新增一個輕量級的查詢，找出所有 `title = '[System] Pending Telegram Alert'` 且 `status = 'todo'` 的任務。
*   **發送與核銷**：嘗試透過 `telegram_service.send_message` 發送。若發送成功，將該任務狀態更新為 `"done"`。若失敗則維持 `"todo"` 留待下次處理。

## 🛡️ 邊界防禦與原則對齊 (Defensive Checks)
*   **避免無限遞迴**：當 `task_dispatcher` 嘗試發送 Pending 任務時，若再次遇到 Timeout，`telegram_service` 會察覺這是補發操作（可透過參數傳遞），避免再次將其重複寫入 `archon_tasks` 造成無限增生。
*   **SSOT 遵循**：不新增任何資料表，完全複用現有的 `archon_tasks` 狀態機機制。

## 🧪 自動化公證 (Automated Verification)
*   新增 `tests/services/test_telegram_persistence.py`。
*   **斷言 1 (Mock Blackout)**：模擬 `httpx` 拋出連線失敗，斷言系統確實將訊息寫入 `archon_tasks` 且狀態為 `todo`。
*   **斷言 2 (Mock Recovery)**：模擬呼叫 `task_dispatcher` 且網路恢復，斷言訊息成功送出，且該任務狀態成功轉為 `done`。
