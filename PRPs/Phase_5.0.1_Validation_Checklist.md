# Phase 5.0.1 驗證步驟與檢查清單 (Validation Checklist)

> **建立日期**: 2026-05-14
> **目的**: 記錄與確保 Phase 5.0.1 模型降級 (Downgrade to gemini-3.1-flash-lite) 的穩定性，並提供後續的系統監控標準。

## 🚦 基礎服務驗證 (Service Health Check)
- [x] **確保所有容器穩定運行 (Up / Healthy)**:
  執行指令：`docker compose --profile backend --profile frontend --profile enduser --profile agents ps`
  確認以下 5 個服務皆為 `Up (healthy)` 狀態：
  - `archon-server` (Port 8181)
  - `archon-agents` (Port 8052)
  - `archon-mcp` (Port 8051)
  - `archon-ui` (Admin UI)
  - `enduser-ui` (End-User UI)

- [x] **確保無 500/503/429 崩潰日誌**:
  執行指令：`docker compose logs --tail=20 | grep -i error`
  （已確認無相關崩潰錯誤）。

## 🌐 網頁介面可用性驗證 (UI Availability)
- [x] **Admin UI (戰情室與管理端)**
  * URL: [http://localhost:3737](http://localhost:3737)
  * 動作：登入並確認 RAG 設定、AI 任務指派與進度條是否正常。
- [x] **End-User UI (客戶與業務端)**
  * URL: [http://localhost:5173](http://localhost:5173)
  * 動作：確認行銷/業務儀表板、Leads 管理與通訊功能是否正常渲染。
- [x] **API Health 端點**
  * URL: [http://localhost:8181/health](http://localhost:8181/health)
  * 動作：確認後端 API 伺服器正常回應 200 OK。

## 🤖 模型與任務驗證 (Model & Workflow Verification)
- [x] **確保模型 SSOT 正確套用**:
  在 `python/src/server/config/model_ssot.py` 中確認 `DEFAULT_TEXT` 與 `DEFAULT_PRO` 皆為 `models/gemini-3.1-flash-lite`。
- [x] **Multi-Agent 工作流無阻礙 (429 Bypass)**:
  執行指令：`make test-be`，並確認 `test_phase53_bob_to_charlie_workflow` 成功通過，證明已突破 20 RPD 的限制。

---

## 🕒 背景監控 (Scheduler Integration)
為了長期監控系統是否因為 API 連線問題或配置錯誤而陷入異常，已將上述檢查的核心邏輯（如健康度與模型一致性檢查）整合進 `Clockwork` (Scheduler Service)。
- **排程頻率**: 每 60 分鐘 (依賴 `SCHEDULER_PROBE_INTERVAL_MINS` 參數)。
- **日誌追蹤**: Scheduler 會將檢查結果記錄至 `system_logs` 資料表中，標記來源為 `clockwork-scheduler`。