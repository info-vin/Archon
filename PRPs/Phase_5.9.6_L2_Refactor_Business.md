# Phase 5.9.6 L2 Refactor: Business Patrol

## 1. 摘要 (Summary)
為延續 Phase 5.9.5 的 L2 核心治理精神，本階段針對原本高達 372 行的「大雜燴」模組 `business.py` 進行了深度拆解。
原本的 `business.py` 混合了「行銷業務 (Leads/Market)」、「系統守門員 (Sentinels)」以及一堆無實質邏輯的「報告轉接器 (Wrappers)」。

## 2. 目標與變更 (Goals & Changes)
1. **行銷與業務 (Leads & Market) 獨立**：建立 `leads_patrol.py` 專職處理 `run_auto_fetch_leads`, `run_prune_stale_leads`, `run_daily_market_report`。
2. **監控與主動防禦 (Sentinels) 獨立**：建立 `sentinel_patrol.py` 專職處理 `analyze_token_usage`, `run_business_sentinel`, `run_api_deprecation_scan`。
3. **消滅冗餘轉接 (Kill Wrappers)**：在 `scheduler_service.py` 中，將原本轉發給 `business.py` 再轉發給 `report_service.py` 的邏輯，改為直接呼叫 `report_service` 執行。
4. **維持相容性**：保留了 `scheduler_service.py` 的對外 alias (`run_business_sentinel` 等) 確保 `admin_api` 與 `internal_api` 能夠正常呼叫，達成無斷層遷移。

## 3. 成效 (Outcomes)
成功消滅了巨獸檔案，並且兩個新檔案都維持在 100~250 行的最佳狀態。系統測試已通過，確保重構品質無虞。
