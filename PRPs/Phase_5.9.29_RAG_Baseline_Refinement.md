# Phase 5.9.29: RAG Baseline Refinement & Keyword Optimization

## 目標 (Goal)
優化潛在客戶 (Leads) 篩選的精準度，將及格率從 0 提升到合理區間 ($\ge 0.65$)。透過淨化 `baseline_embedding` 排除開發指令雜訊，以及將搜尋關鍵字精緻化為高技術痛點關聯詞，達成精準獲取。

## 預計修改檔案 (Files to Modify)
1. **`python/src/server/schemas/settings.py`**
   - 更新 `CrawlerJobConfig` 的 Pydantic 預設 Fallback 關鍵字：將 `Marketing` 換成 `AI行銷自動化`，將 `Sales` 換成 `智慧客服`。
   - 新增兩個額外的精準關鍵字：`AI自動化流程`、`大語言模型應用`。
   - 最終關鍵字陣列將擴展為 7 項：`Python, AI, AI行銷自動化, 智慧客服, 數據分析, AI自動化流程, 大語言模型應用`。
2. **`python/src/server/services/job_board_service.py`**
   - 重構 `_get_baseline_embedding()`。
   - 將原本的 9.3% 雜訊切片（包含開發部署備註）縮減為僅佔 **4.6%** 的純淨核心能力描述（僅擷取 `### Knowledge Base Tools` 到 `### Document Management` 的純淨區段）。

## 自動化驗證計畫 (Automated Verification)
1. **單元與整合測試**
   - 撰寫測試腳本模擬 RAG 比對。驗證高契合度職缺（如 AI/Python）經 `_infer_need()` 降維後的相似度得分高於 `0.65`。
   - 驗證低契合度職缺（如純文書）相似度得分低於 `0.65` 被正確過濾。
2. **品質門禁檢查**
   - 執行 `make lint-be` 驗證 Python 程式碼風格與強型別無誤。
   - 執行 `make test-be` 確保無任何功能回歸。
   - 執行 `make phase-audit` 確保不引入新的硬編碼違規。

## 成功標準 (Definition of Done)
- **實體分數達標**：測試資料中，高契合度的虛擬職缺痛點計算出的 Cosine Similarity 必須高於 `0.65` (達成 0 -> 1 突破)。
- **門禁安全綠燈**：`make test-be` (600+ 測試) 與 `make phase-audit` (SSOT 檢驗) 亮起綠燈。
