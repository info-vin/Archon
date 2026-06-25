# Phase 5.8.0: Semantic Infiltration - 實作與防禦性驗證計畫 (Implementation & Validation Plan)

> **核心原則：拒絕樂觀路徑 (No Happy Path)**
> 任何跨網路、跨服務的架構，在被實體程式碼證明可行之前，皆視為「必定失敗」。在進入 Godot 視覺與遊戲邏輯開發前，必須先以 Python Probe 腳本貫穿整條基礎架構序列。

## 階段一：架構序列物理探針驗證 (Python Pipeline Probing)
**目標**：不寫任何 API，不寫任何前端。直接寫一支獨立的 Python 探針腳本，驗證 TDD 1.2 節定義的資料流是否在現實網路環境中存活。

*   **任務 1.1：建立探針腳本 (`scripts/probe_rag_pipeline.py`)**
    *   **HF 向量化驗證**：打 Hugging Face Serverless API，測試 `768` 維度的 Embedding 模型是否超時或觸發 429 Rate Limit。
    *   **Supabase RPC 驗證**：透過 `supabase-py` 直接呼叫 `hybrid_match_chunks` 預存程序 (模擬資料)，確認 `vector(768)` 運算與 `metadata` 回傳無誤。
    *   **CDN 穿透驗證**：讀取回傳的 `metadata` GitHub 網址，實體發送 HTTP GET。**初期探針測試僅需抓取極小型的「範例 JSON (Minimal Mock)」**，目的是以最低成本證明網路通聯 (Connectivity) 與 CORS 無阻礙，而非盲目下載巨型檔案浪費頻寬。
    *   **斷言 (Assert)**：腳本必須輸出各階段的延遲 (Latency)。若總耗時超過 3 秒，或遇到任何網路中斷，Probe 視為失敗，計畫退回重審。

## 階段二：後端 API 與資料庫部署 (Backend & Database)
**門禁**：必須在階段一 `probe_rag_pipeline.py` 連續亮綠燈後方可執行。

*   **任務 2.1：資料庫遷移**
    *   將 `migration/0.2.2/26_rag_hybrid_search_rpc.sql` 推上 Supabase。
    *   確保 `archon_crawled_pages` 表格的 `vector(768)` 檢索索引有效。
*   **任務 2.2：FastAPI 服務層 (`rag_game_service.py`)**
    *   將階段一驗證過的 Probe 邏輯封裝為非同步 Service。
    *   加入 `BaseRepository` 的錯誤重試防護網 (防禦 Supabase Connection Terminated)。
*   **任務 2.3：FastAPI 路由層 (`rag_game_api.py`)**
    *   開放 `POST /api/game/rag/query`，供 Godot 呼叫。

## 階段三：Godot 無頭公證與邏輯實作 (Godot Headless TDD)
**門禁**：後端 API 可透過 `curl` 穩定取得 GitHub JSON 後方可執行。

*   **任務 3.1：網路通訊層 (`BackendClient.gd`)**
    *   實作非同步 `HTTPRequest`，接駁 FastAPI 路由。
    *   **錯誤自癒 (Fallback)**：必須實作 HTTP 500/Timeout 的重試機制與錯誤代碼拋出。
*   **任務 3.2：卡牌狀態機 (`DeckManager.gd`)**
    *   實作 TDD 2.3 節的**核心戰鬥數學驗證公式** (AP 計算、純淨度 P 計算、交付傷害 D 計算)。
*   **任務 3.3：Headless 零依賴測試**
    *   使用原生 `HeadlessRunner.gd` 進行測試，測試前**強制清除 `user://savegame.save`**。
    *   模擬接收 JSON，斷言 (Assert) 公式計算結果是否與預期傷害完全一致。

## 階段四：AI 美術資產與視覺串接 (Art Integration)
**門禁**：Headless 測試算數與狀態移轉 100% 通過後方可執行。

*   **任務 4.1：SDXL/Flux 圖像生成與裁切**
    *   根據 TDD 5.3 的 AI 提示詞，生成無版權的高品質背景與卡牌 2D 貼圖。
*   **任務 4.2：事件佇列與 Tween 動畫 (`GameBoard.tscn`)**
    *   實作 EventQueue 消費模式，將 `DeckManager` 發出的純邏輯快照，轉化為 UI 卡牌的緩動 (Tween) 動畫與打擊音效。
