# PRP: Phase 4.6.14 - 全系統 UI 加固與錯誤恢復機制 (System-Wide UI Hardening)

> **狀態**: ✅ 結案 (物理驗證通過)
> **日期**: 2026-03-18
> **目標**: 解決後端容器啟動延遲與配置錯誤導致的前端「白屏」或「掛起」問題，強化系統韌性。

## 1. 核心實作內容

### A. 前置診斷攔截 (Backend Startup Protection)
*   **組件**: `BackendStartupError.tsx`
*   **機制**: 在 `App.tsx` 頂層注入連通性檢查。若後端 API 無法在 5 秒內響應，自動觸發全螢幕錯誤攔截器。
*   **引導**: 提供 Docker 指令 (`docker compose up --build -d`) 與 `.env` 檢查建議（區分 SERVICE_KEY 與 ANON_KEY）。

### B. 視覺層加固 (Visual Hardening)
*   **戰情室風格**: 在 `ManagerNexus.tsx` 與 `SystemHealthDashboard.tsx` 引入 `backdrop-blur-sm` 與 `bg-black/90`，營造「核心戰略空間」感。
*   **互動反饋**: 統一使用 `lucide-react` 圖示與 `RefreshCw` 動態旋轉效果，確保所有非同步操作都有物理反饋。

### C. 佈局彈性 (Layout Resilience)
*   **Min-Width 策略**: 修正所有彈窗 (Modal) 的 `max-w` 屬性，確保在不同解析度下不會破版。
*   **滾動鎖死防禦**: 移除巢狀滾動區域中不必要的 `overflow-hidden`。

## 2. 驗證清單
- [x] 手動停止 Docker 容器，前端應正確顯示 `BackendStartupError` 蓋板。
- [x] 模擬 `.env` 缺少 `SERVICE_KEY`，蓋板應給出正確建議。
- [x] 在 4K 與 行動端螢幕測試佈局對齊。
