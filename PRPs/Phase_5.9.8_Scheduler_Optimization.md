# Phase 5.9.8 Scheduler Optimization (Draft)

> **註記**：此排程最佳化計畫目前處於草稿階段，等待下週收集足夠 WAF 阻擋與系統穩定度資料後再行檢討實作。

## 觀察與問題描述
目前排程器 (`scheduler_service.py`) 將主要任務集中在 UTC 00:00 (台灣時間早上 08:00) 執行。這導致了以下問題：
1. **104 WAF 尖峰阻擋**：早上時段為求職網站防爬蟲策略最嚴格的尖峰期，導致 `alice_auto_fetch` 與 `bob_auto_fetch` 頻繁遭 WAF 攔截，回傳空資料。
2. **任務衝突**：排程集中在同一時段觸發，可能導致背景清理程式 (Pruning) 誤殺剛建立但尚未被 Agent 領取的任務 (Cancel/Archive 衝突)。

## 預定調整方案 (待檢討)
為解決上述問題，預計將排程時間分散化，避開早上尖峰：
- `alice_auto_fetch` / `bob_auto_fetch`：調整至 **UTC 07:00 (台灣時間 15:00)**。
- `daily_executive_summary`：調整至 **UTC 08:30 (台灣時間 16:30)**。
- `weekly_executive_summary`：每週五 **UTC 10:00 (台灣時間 18:00)**。
- `monthly_executive_summary`：每月 1 號 **UTC 10:00 (台灣時間 18:00)**。
