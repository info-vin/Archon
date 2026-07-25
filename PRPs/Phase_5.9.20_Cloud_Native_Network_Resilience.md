# Phase 5.9.20: Cloud Native Network Resilience & WAF Evasion

## 🎯 目標 (Objective)
解決部署至 Hugging Face (Monolith 單一容器架構) 時遭遇的三大實體基礎設施阻礙：
1. `AGENTS.md` 上下文遺失導致的檔案讀取錯誤。
2. `WorkflowEngine` 的 `archon-agents` DNS 解析失敗導致 Agent Service 斷線。
3. 104 人力銀行 WAF 針對 Datacenter IP 進行的嚴格速率限制 (403 Forbidden)。

## 🛡️ 核心守則 (Principles)
- **不要改 A 壞 B (Zero Regression)**：所有修改必須隔離在 HF 部署腳本與爬蟲邏輯內，確保 Docker Compose 本機開發環境完全不受影響。
- **不要硬編碼 (No Hardcoding)**：爬蟲的 WAF 降頻秒數必須導入 `SettingsService` 與 `CrawlerJobConfig`，落實 SSOT (Single Source of Truth) 原則。
- **物理穿透驗證 (Physical Verification)**：以真實日誌數據為基礎，不抱持樂觀路徑幻想。

## 📝 實作步驟 (Implementation Steps)

### Step 1: 修復 HF 部署腳本 (`scripts/deploy_to_hf.sh`)
- **[異常1]** 補回被遺漏的 `AGENTS.md`：
  - 在 `git checkout "$SOURCE_BRANCH" -- ...` 區段，新增 `git checkout "$SOURCE_BRANCH" -- AGENTS.md`。
- **[異常2]** 覆寫 Agent Service 的 DNS 盲區：
  - 於寫入 `Dockerfile` 的階段 (Step 4.5)，新增 `echo "ENV AGENTS_SERVICE_URL=http://127.0.0.1:8052" >> Dockerfile`。
  - 這能確保單一容器架構下，FastAPI 能透過 localhost 找到 Agent 服務，而不會影響本機 Docker Compose 的 `archon-agents` 解析。

### Step 2: SSOT 爬蟲配置抽離 (`python/src/server/schemas/settings.py`)
- **[異常3]** 為了不寫死延遲時間，擴充 `CrawlerJobConfig`，新增 WAF 降頻設定：
  - `crawler_waf_delay_min: float = Field(default=60.0, alias="CRAWLER_WAF_DELAY_MIN")`
  - `crawler_waf_delay_max: float = Field(default=90.0, alias="CRAWLER_WAF_DELAY_MAX")`

### Step 3: WAF 降頻與指紋輪替實作 (`python/src/server/services/job_board_service.py` & `job104_client.py`)
- 修改 `job_board_service.py`，將原本寫死的 `await asyncio.sleep(random.uniform(2.0, 4.0))` 替換為動態讀取 `config`：
  `await asyncio.sleep(random.uniform(config.crawler_waf_delay_min, config.crawler_waf_delay_max))`
- 修改 `job104_client.py`，建立支援的 TLS Fingerprint 清單 (如 `"chrome110", "chrome120", "safari15_3", "safari17_0", "edge101"`)，並在每次 `requests.Session()` 初始化時透過 `random.choice()` 動態抽換，降低指紋特徵的一致性。

## 🧪 驗證計畫 (Verification Plan)
- 透過 `make test-be` 確保 `CrawlerJobConfig` 的新增欄位不會破壞既有 Pydantic 解析。
- 推送至 Hugging Face 觀察容器啟動日誌，確認 `AGENTS_SERVICE_URL` 正確生效，且 `job_board_service` 不再報出 `/app/AGENTS.md` missing error。

## ✅ 執行狀態 (Execution Status)
- **完成日期**：2026-07-25
- **狀態**：✅ 已完成 (Completed)
- **備註**：已完成全部實作，通過 612 項後端單元測試，並已成功合併至 `dev/twins` 觸發 GitHub Actions 部署至 Hugging Face 雲端機房。
