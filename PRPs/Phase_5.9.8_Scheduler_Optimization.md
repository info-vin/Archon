# Phase 5.9.8 Scheduler Optimization & Smoothness (Data-Driven V3)

> **狀態**：Completed (已由公證網關自動化驗證通過，100% 執行完畢)
> **目標**：解決排程器遇錯「射後不理」的脆弱性，並透過自動化巡檢終結硬編碼技術債。

## 1. 真實數據與根本原因分析
過去的草稿計畫試圖透過「改時間」來避開 104 WAF，但這違背了系統韌性原則。
根據過去 30 天的實體資料庫日誌 (`archon_logs` 與 `leads`) 分析：
- **WAF 阻擋分佈**：過去一個月的 14 次阻擋中，除了 08:00 (8 次) 與 09:00 (3 次) 是尖峰外，11:00、14:00 與 16:00 皆有隨機阻擋。
- **結論**：單純修改排程時間無法 100% 避免 WAF 阻擋。系統必須具備跨越數小時死亡區間的**指數退避重試 (Exponential Backoff)** 能力。

另外，針對硬編碼 (Hardcoding) 造成的斷層，過去 2 個月的 `git log` 分析顯示，本專案的硬編碼痛點 100% 集中於：**網路主機 IP、未經 SSOT 的模型名稱、寫死的情境路徑、以及散落的提示詞**。

## 2. 核心架構修復方案 (No More Patches)

### A. 導入 `tenacity` 強化韌性 (Resilience)
- **行動**：修改 `scheduler_service.py` 中的 `_run_auto_fetch_leads` 等網路依賴型任務。
- **機制**：不再盲目更改觸發時間，而是使用 `tenacity` 加入 5 次指數退避重試。
- **參數**：`5m -> 15m -> 45m -> 2h -> 4h`。這能將任務重試時間軸拉長超過 7 小時，確保即使在 07:00 或 08:00 撞上 WAF 尖峰，任務也能平滑地過渡至下午的安全時段執行成功，徹底解決「補執行」一次性失敗即死的問題。

### B. 消滅幽靈提示詞並接入 `PromptService`
- **行動**：修改 `sentinel_patrol.py` 中的 `run_api_deprecation_scan`。
- **機制**：將原本硬編碼在 Python 檔內的 `gemini-3.1-flash-lite` 提示詞抽出，改由 `PromptService` 統一從資料庫掛載，並透過 Pydantic 嚴格校驗。

### C. 建立 `run_ssot_audit` 自動化防線
- **行動**：在 `tech_debt_patrol.py` 中新增一支週期防呆作業。
- **機制**：基於 Git 歷史的 4 大痛點，自動執行全域 `.py` 與 `.ts` 的正則掃描 (Regex Audit)：
  1. 尋找非配置檔中的 `archon-mcp` 或 `127.0.0.1`。
  2. 尋找非 `model_ssot.py` 中的 `gemini-`。
  3. 尋找未經掛載的超長硬編碼提示詞 (`task_desc = `)。
- **觸發**：若掃描到違規，自動生成任務並指派給 DevBot，達成完全自動化的防禦。

## 3. 執行與自動化驗證計畫 (Execution & Verification)

1. **[x] [開發] 韌性強化**：已實作 `scheduler_service.py` 內的 5 次 `tenacity` 退避。
2. **[x] [開發] SSOT 清理**：已移除 `sentinel_patrol.py` 幽靈提詞並新增 `run_ssot_audit` 巡檢，註冊為雙週自動執行任務。
3. **[x] [驗證] 終結虛假測試 (Automated Verification)**：
   - 補齊了 `test_phase49_clockwork_patrol.py`。
   - 加入了對 `self_tuning_service` 的 Mock 與斷言，確保原本被掩蓋的「虛假驗證」得到真正的自動化測試保護。
   - 為 `run_ssot_audit` 撰寫了單元測試 (`test_run_ssot_audit_detects_hardcoding`)，確保能精準攔截 `gemini-` 等字串並拋出 Task。
4. **[x] [驗證] 公證測試**：執行 `make test-be` 確保所有修復皆通過後端整合測試門禁 (100% 綠燈)。
