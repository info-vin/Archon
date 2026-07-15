# Phase 5.9.3: 104 商機萃取與雙週階層瘦身 (Lead Gen & Tiered Pruning)

## 🎯 階段目標 (Phase Goal)
將原本的 Dummy 爬蟲任務升級為真實的 104 職缺狩獵與商機萃取引擎，並建立動態的三級資料庫容量清理 (Tiered Pruning) 機制，確保系統在長期運行下不會因為容量爆炸而崩潰。

## 📝 實作細節 (Implementation Details)

- `[x]` **104 職缺狩獵與商機萃取 (True RAG Lead Gen)**:
  - **物理向量化**：`job_board_service.py` 爬蟲取得職缺資訊與萃取 `identified_need` (純字串) 後，主動讀取 `AGENTS.md` 的核心功能區塊並將其向量化。
  - **餘弦相似度門禁 (Cosine Similarity)**：引入了真實的數學計分機制，並設定閥值。大於等於閾值視為高價值商機，寫入 `leads` 表格；小於則自動捨棄並留存日誌。
  
- `[x]` **雙週階層瘦身 (Tiered Database Pruning)**:
  - 建立 `PruningConfig` 實踐單一事實來源 (SSOT)，消除所有魔法數字。
  - **排程週期校正**：將 `infrastructure_audit` 排程移至 Category 4 (雙週維護, Stateful Bi-weekly Maintenance)。
  - **三級警戒實裝**：透過 RPC `get_db_size_mb` 獲取真實資料庫容量，執行三級清理：
    - **Level 1 (< 50%)**：常規清理。
    - **Level 2 (50-79%)**：加強清理 (提前清理日誌與 dormant 商機)。
    - **Level 3 (>= 80%)**：求生模式 (激進清理日誌、孤兒向量與爬蟲快取)。

- `[x]` **底層 SQL 擴充與修復**:
  - 建立 `migration/0.2.2/100_add_tiered_pruning_rpcs.sql`。
  - 為 Supabase 提供安全預存程序 (RPC)，解決 REST API 無法直接執行 `pg_database_size()` 以及複雜跨表刪除的需求。

## 🛡️ 驗證與公證 (Verification)
- `[x]` 完成 MyPy 靜態型別與架構對帳，確保 `Model.model_validate()` 正確反序列化參數。
- `[x]` 所有 E2E 與單元測試 (`make test-be`) 亮綠燈。
