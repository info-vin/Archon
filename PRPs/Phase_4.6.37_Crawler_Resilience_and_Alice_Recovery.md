# Phase 4.6.37: Crawler Resilience and Alice Recovery (爬蟲韌性與 Alice 演示自癒)

## 1. 物理斷層診斷
根據數據分析，目前的 104 爬蟲在 Docker 環境下可用性為 0%：
- **原因 A**: 104 WAF 識別並阻斷了資料中心 IP。
- **原因 B**: 3 月底的重構移除了所有 Mock 緩衝，導致連線失敗時 Alice 的 Persona 體驗直接歸零。

## 2. 落地實作紀錄 (Physical Realization)
- **數據緩衝**: 🟢 恢復 `MOCK_JOBS` 並填入具備實體案場價值的歷史資料（不再是虛構資料）。
- **邏輯降級**: 🟢 修正 `search_jobs`，當 API 逾時或回傳非 JSON 時，自動回傳緩存資料。
- **指紋對齊**: 🟢 採用 Windows 10 x64 物理指紋，減少被 WAF 標記機率。

## 3. 驗證數據
- **演示成功率**: 物理保證 100% 產出 Leads（實體或緩存）。
- **UI 反饋**: 驗證 `Connection Limited` 警告在 API 失效時能正確顯示。

## 4. 結案狀態
- **狀態**: 🟢 **100% 物理落地** (2026-04-10)
