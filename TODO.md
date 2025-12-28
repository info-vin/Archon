# Archon 專案開發藍圖

本文件旨在規劃 Archon 專案的下一階段開發，核心目標是將 Agent 自動化與 RAG (檢索增強生成) 功能深度整合到 endUser-ui 中，實現人機協作的智慧任務管理。

---

## 技術債與未來優化 (Technical Debt & Future Optimizations)

### 為詞嵌入服務增加 API 金鑰自動故障轉移 (Failover) 功能
- **目標**: 增強 `embedding_service.py` 的健壯性 (robustness)。
- **理由**: 目前當首選的詞嵌入提供商（如 OpenAI）因額度耗盡 (`insufficient_quota`) 而失敗時，整個流程會中斷。此功能將允許系統自動嘗試下一個已配置的、可用的提供商（如 Gemini），從而提高系統的穩定性和可靠性。
- **影響**: 在此任務完成前，使用者需要手動在 RAG 設定中更換模型提供商來應對 API 額度問題。
- **開發計畫**:
    - **1. 修改設定**: 在 RAG 設定中，允許使用者定義一個備援 (Fallback) 的詞嵌入服務提供商。
    - **2. 修改 `embedding_service.py`**:
        - 調整 `create_embeddings_batch` 函式的邏輯，使其可以接受一個供應商列表。
        - 當使用主要供應商失敗後（特別是捕捉 `EmbeddingQuotaExhaustedError` 等嚴重錯誤時），記錄錯誤並自動使用備援供應商重試。
        - 如果所有供應商都失敗，才回傳最終的失敗結果。