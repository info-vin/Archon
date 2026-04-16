# Phase 4.6.36: Network Resilience (全網路環境適應與金鑰硬化)

## 1. 物理斷層診斷
在 Phase 4.6.33 之後，系統陷入了內部 Docker DNS 與外部 Host DNS 的連線衝突：
- **現象**: 瀏覽器存取 5173 時，API 請求指向 `archon-server` 導致 `ERR_NAME_NOT_RESOLVED`。
- **安全性**: `VITE_SUPABASE_ANON_KEY` 被錯誤掛載為 `SERVICE_KEY`，造成 Session 污染。

## 2. 落地實作紀錄 (Physical Realization)
- **前端硬化**: 🟢 在 `apiClient.ts` 注入 Pattern 7 邏輯：瀏覽器環境自動將 `archon-server` 改寫為 `localhost`。
- **安全性修正**: 🟢 修正 `docker-compose.yml` 變數掛載，回歸 `ANON_KEY` 標準。
- **護衛測試**: 🟢 建立 `apiClient.test.ts`，物理模擬雙環境並驗證改寫邏輯。

## 3. 驗證數據
- **護衛測試結果**: `✓ apiClient Network Resilience (2 tests) 🟢 PASS`。
- **Docker 日誌**: `archon-server` 無 403/500 報錯。

## 4. 結案狀態
- **狀態**: 🟢 **100% 物理落地** (2026-04-10)
