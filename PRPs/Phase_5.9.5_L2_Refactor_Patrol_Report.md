# Phase 5.9.5 L2 Refactor: Patrol & Report Service

## 1. 摘要 (Summary)
為確保系統架構維持在極度健康的狀態，本階段將對在先前的 L2 模組化行動中「存活」下來，但已逼近 400 行生死線的兩支核心檔案進行重構：
- `python/src/server/services/scheduler/jobs/patrol.py` (392 行)
- `python/src/server/services/report_service.py` (390 行)

## 2. 目標 (Goals)
1. **單一職責原則 (SRP) 實踐**：將 `patrol.py` 中與健康探測無關的「資料清理 (Cleanup)」與「技術債稽核 (Tech Debt Audit)」邏輯，抽取為獨立的模組。
2. **消滅重複代碼 (DRY 原則)**：將 `report_service.py` 中，高達 95% 相似的週報與月報 Map-Reduce 邏輯進行提煉整合。同時拆解臃腫的上下文收集函數。
3. **行數門禁**：將上述兩支檔案的行數雙雙壓制在 250 行以內。
4. **功能驗證**：確保重構後所有的自動化測試 (`make test-be`) 依然亮綠燈，絕不容許「改A壞B」的斷層出現。

## 3. 執行細節 (Implementation Details)
- 建立 `cleanup_patrol.py`，專職處理過期 Leads、Crawled Pages、Sources 與 RAG Orphans 的清理。
- 建立 `tech_debt_patrol.py`，專職掃描過期的 PRPs 與 Scripts 並指派任務給 DevBot。
- 修改 `scheduler_service.py`，正確引入新的 patrol 模組。
- 修改 `report_service.py`，提取 `_gather_leads_summary`, `_gather_token_summary` 等輔助函數，並建立 `_execute_map_reduce_summary` 統包週報與月報的產生流程。
