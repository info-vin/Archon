# Phase 5.2.0: QA 全自動化驗證與 MBT 硬化實作計畫 (修正版)

## 📋 核心願景
本計畫旨在將 11 大「手動驗收盲區」與「環境邊界限制」徹底轉化為 CI 流程中的自動化阻斷點。我們拒絕「人工自檢」的低效，改以 **MBT (狀態機邏輯遍歷)** 與 **VRT (像素級視覺比對)** 為雙翼，並利用正式穩定的 **Gemini 3.1 系列模型** 擔任「視覺與語音裁判」。

---

## 🔍 技術標準：拒絕幻想與隨便開發

### 1. 模型標準 (Single Source of Truth)
*   **Supervisor (大腦/決策)**: `models/gemini-3.1-flash`
*   **Worker/Judge (裁判/執行)**: `models/gemini-3.1-flash-lite` (Free Tier 友善, 15 RPM / 1000 RPD)
*   *備註：嚴格對齊 [model_ssot.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/config/model_ssot.py)，停用所有 `-preview` 預覽版後綴。*

### 2. 環境與物理邊界限制 (Environment Boundaries)
> [!IMPORTANT]
> **拒絕快樂路徑與幻想，以下 4 大物理邊界必須在代碼中被強制約束：**
> 
> 1.  **資料庫純雲端隔離 (Database Cloud-Isolation)**：由於專案無本地 DB 容器且直接連接 Supabase Cloud，在 CI 中驗證 Schema 變更時，必須在 CI 內部臨時拉起一個極簡 `postgres:alpine` 本地容器作為**影子資料庫 (Shadow DB)**。嚴禁對遠端 Supabase 進行暴力寫入。
> 2.  **免 Keychain 身分注入 (OS Keychain Bypass)**：Docker / CI 容器內無法訪問 Mac/Linux 的本地加密 Keychain 服務。Playwright 必須繞過實體 Profile 登入，改由在啟動前從 JSON 格式的 [admin_storage_state.json](file:///Users/vincenta/GoogleKwok022/Archon/.playwright/admin_storage_state.json) 直接將 Cookie 與 LocalStorage 物理注入 `BrowserContext`。
> 3.  **無音效卡音軌攔截 (Audio Byte-Stream Interception)**：CI/Docker 環境無實體聲卡。驗證 TTS 播放時，不可依賴播放器 or 麥克風，必須直接在 Playwright 或後端測試中攔截 `/api/audio/generate` 的二進位 **Wav Byte Stream**。
> 4.  **Vite Proxy 依賴守護 (Vite Server Guard)**：Playwright 測試執行前，必須確保 Vite Server (Port 5173) 已被正確編譯並執行（如透過 `pnpm run build && pnpm run preview`），以避免 `Connection Refused` 錯誤。

---

## 🛠️ 實作里程碑與 11 大盲區攻克清單

### Milestone 1: 基礎設施與網路邊界 (Infrastructure)
*   **任務 5.2.0.1 (Rule 11 - Supabase Shadow Deploy)**：建立 `scripts/verify_migrations.py`。在 CI 流程中，自動啟動本機臨時 `postgres` 容器執行 `migration/` 下的 SQL，並導出 schema 與 Supabase 生產環境進行 diff 對比，若有語法或結構未授權變更則阻斷。
*   **任務 5.2.0.2 (Rule 7 - DNS Leak Probe)**：實作 `scripts/probe_dns_leak.sh`。掃描編譯後的前端 `dist/` 目錄，嚴格禁止出現 `_kong`、`localhost:8000` 或 Docker 內部 IP (172.x)，防止外網載入失敗。
*   **任務 5.2.0.10 (MCP Health & Tool Schema Probe)**【新增】：建立 `scripts/verify_mcp_health.py`。在 CI 中拉起 `archon-mcp` 並向 `http://localhost:8051/health` 進行健康檢查，同時遍歷所有註冊的 MCP Tools，確保 tool schemas 無 JSON/Pydantic 語法錯誤。

### Milestone 2: 視覺保真度與 MBT 狀態硬化 (Visual & Logic)
*   **任務 5.2.0.3 (Rule 60 - Chart Animation Hardening)**：在 E2E 測試基底 [systemFixtures.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/tests/playwright/fixtures/systemFixtures.ts) 中，強制攔截 Recharts 屬性並注入 css 將動畫過渡時間設為 `0s` (或設 `isAnimationActive={false}`)，確保 VRT 截圖時機點 100% 穩定。
*   **任務 5.2.0.4 (Multi-Agent UI Vision Audit)**：實作 `scripts/vision_judge.py`。利用 Gemini 3.1 視覺裁判，自動判定星型群聊在 UI 上的 WhatsApp 氣泡是否重疊、Avatar 是否正確變色。
*   **任務 5.2.0.5 (MBT Coverage Expansion)**：將 `promptMachine` 的 XState 狀態機驗證推廣至 `ApprovalsPage`。自動遍歷「500 報錯、網路超時、連續併發點擊」等極端狀態。

### Milestone 3: 感官與物理互動 (Sensory & Interaction)
*   **任務 5.2.0.6 (TTS Audio Loopback)**：建立 `tests/server/test_audio_semantic_loop.py`。自動抓取產生的 Wav 二進位流，傳送給 Gemini 3.1 進行語意辨識，確認「音訊內容正確且無靜音」。
*   **任務 5.2.0.7 (Rule 9 - Scroll Lockup Static Interceptor)**：開發 `scripts/check_scroll_lockup.py`。採用極簡 Standalone 掃描器，靜態掃描前端 TSX，從源頭偵測並阻斷 `min-h-screen` 與 `overflow-y-auto` 的衝突配置，消滅行動端捲動死鎖。

### Milestone 4: 身分、預算與 AI 非確定性 (Identity, Budget & AI)
*   **任務 5.2.0.8 (Rule 13 - Session Injection Service)**：實作自動化 Session 注入工具。在 Playwright 測試啟動前，自動將預先錄製的加密 Cookie 注入 `BrowserContext`，擺退對宿主機 OS Keychain 的依賴。
*   **任務 5.2.0.9 (AI Semantic Invariants)**：建立 `scripts/llm_judge_content.py`。針對 AI 生成的 Insights 與文章，利用 Supervisor 模型進行語意斷言，驗證其是否符合商業目標與字數限制。
*   **任務 5.2.0.11 (Budget & Token Threshold Banner)**【新增】：在 Playwright MBT 中，Mock 前端 API 回傳 Token 使用量超標 (Exceeds Target Budget)，並撰寫斷言驗證前端是否正確彈出「預算超標警告橫幅 (Budget Limit Warning Banner)」。

---

## ⚠️ 物理公證標準

所有任務必須通過 **`make audit-qa`** 終極指令。若任何一項盲區測試未通過，該 PR 絕對不可合併。

```makefile
# Makefile 整合範例
audit-qa: lint
	@echo "🔍 Performing Phase 5.2.0 QA Physical Audit..."
	@python scripts/verify_migrations.py
	@bash scripts/probe_dns_leak.sh
	@python scripts/check_scroll_lockup.py
	@python scripts/verify_mcp_health.py
	@uv run pytest python/tests/server/test_audio_semantic_loop.py
	@cd enduser-ui-fe && npx playwright test
	@echo "🟢 [PHYSICAL PARITY REACHED] 100% 全系統無盲區通過！"
```

## 💰 資源消耗預估
*   **Token**：單次 CI 約消耗 15-20 次 Gemini 3.1 Flash-Lite 請求，完全符合 Free Tier (15 RPM) 標準。
*   **時間**：自動化 VRT 與音訊辨識預計增加 2 分鐘 CI 耗時，以換取 100% 的部署信心。
