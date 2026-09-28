# Phase 5.11.22: 零虛假公證與架構死鎖大清洗 (2026-09-26)

## 📌 背景與動機 (Context & Motivation)
在進行 5.11.21 的 Code Review 時，我們追溯了自 Phase 5.11.15 以來的整條架構演進史，發現了一齣因「網路防火牆誤判」引發，並由「虛假測試」層層掩護的災難：
1. **5.11.15~18 (誤診)**：因未查明 Hugging Face 防火牆封鎖，反覆盲猜 IPv6 與路由問題，並宣稱「拒絕虛假修復」。
2. **5.11.19 (萬惡之源)**：新增了 DB 慢速佇列作為備援，卻撰寫了 **100% Mock 資料庫與回傳值的「假測試」**，還用 `except Exception: pass` 吞噬致命崩潰。
3. **5.11.20 (邏輯斷層)**：導入 Vercel Proxy 繞過防火牆，卻忘了 Proxy 逾時會回傳 HTTP 500。由於 Python 端遇 500 即刻中斷，徹底架空了原有的快速重試機制；同時，被丟入 5.11.19 佇列的訊息，在撈取時**完全遺失了 `parse_mode` 狀態**。
4. **5.11.21 (全域死鎖)**：在 Oracle 代理實作了 Map-Reduce 平行擷取，但內部呼叫的 10 個 Service 方法全都是**假非同步 (同步呼叫 `execute_query`)**。實體探針證實，這會造成 Event Loop 發生長達 4.8 秒的「心跳停止 (Starvation)」，並再次用全域 Mock 測試掩護過關。

本階段的唯一目標：**物理拔除這些遮羞布，還原架構真相。**

## 🎯 核心修復目標 (Core Objectives)

### 1. 解除 Event Loop 假非同步死鎖 (Event Loop Unblocking)
- **目標**：修復 `NexusOracleAgent` 的 `gather_nexus_data`。
- **實作**：將所有底層呼叫 (如 `stats_service`、`blog_service.get_pending_reviews_metadata` 等) 統一封裝進 `asyncio.to_thread`，確保 I/O 等待期間交出執行權。
- **門禁**：心跳探針 (`probe_event_loop.py`) 必須在執行期間保持 50ms 穩定跳動。

### 2. 修復 Telegram 狀態遺失與重試架空 (State Restoration & Retry Fix)
- **目標 A (重試架空)**：修改 `telegram_service.py`，當遭遇 `httpx.HTTPStatusError` 且為 5xx (如 Vercel Gateway Timeout) 時，必須觸發 `max_retries` 迴圈的退避重試，而非立刻放棄。
- **目標 B (狀態遺失)**：升級 `_queue_failed_message`，將 `text` 與 `parse_mode` 以 JSON 格式封裝寫入 `archon_tasks.description`，並在 `task_dispatcher.py` 撈出時精準還原。

### 3. 摧毀虛假驗證 (Annihilate Fake Mocks)
- **目標**：重寫 5.11.19 與 5.11.21 的測試。
- **實作**：
  1. 拔除 `test_telegram_persistence.py` 中對 Supabase 的 Mock，強制測試直接連上本地 Docker DB 進行實體讀寫。
  2. 拔除 `test_nexus_oracle.py` 的 `_run_agent` Mock，改為使用 `RunContext` 直接測試 `gather_nexus_data` 工具邏輯。

## 🛡️ 物理公證防線 (Physical Penetration Audit)
- **紅綠燈法則 (Red-Green Law)**：所有新撰寫的測試，必須先「刻意寫錯斷言」展示紅燈 (證明實體穿透無遮蔽)，再修正為綠燈。
- **探針先行 (Probe First)**：實體驗證 Event Loop 心跳無阻塞，方可標記完成。
