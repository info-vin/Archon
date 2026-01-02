name: "Phase 4.0.i: Knowledge Integration (知識庫整合計畫)"
description: |
  本計畫旨在打通知識庫管理 (Admin UI) 與任務執行 (End-User UI) 之間的斷層。
  核心目標是讓 Admin 在後台準備好的知識資源，能夠被一般使用者在建立任務時精確選擇並作為 AI 的上下文。
  這是一個「整合性 (Integration)」階段，重點在於權限傳遞與 UI 連結。

---

## Goal (目標)

**Feature Goal (功能目標)**: 實現在 End-User UI 中選擇並連結既有知識庫項目至特定任務的功能。

**Deliverable (交付成果)**:
1. **API 橋接**: 在 `enduser-ui-fe` 實作獲取知識列表的 API 客戶端。
2. **任務上下文選擇器**: 在 `TaskModal.tsx` 中新增一個知識庫選擇元件 (Selector)。
3. **資料持久化**: 確保任務與知識庫的關聯 ID 正確儲存於資料庫中。

**Success Definition (成功定義)**: 使用者在 `enduser-ui-fe` 建立任務時，能從下拉選單看到 Admin 上傳的檔案（如「產品手冊.pdf」），選取後該 ID 會隨任務傳送至後端。

## User Persona (使用者畫像)

**Target User**: 專案成員 (Member) / 任務指派者。

**Use Case**: 使用者需要 AI Agent 參考一份特定的技術文件來撰寫報告。

**User Journey**:
1. 使用者開啟「新任務」視窗。
2. 點擊「參考知識」下拉選單。
3. 搜尋並勾選「2025_API_Spec.pdf」。
4. 點擊建立，AI Agent 收到任務後自動載入該文件的 Chunks。

## Why (為什麼)

- **消除斷層**: 解決「Admin 準備了資料但 User 用不到」的現狀。
- **提升精準度**: 避免讓 AI 在整個知識庫中漫無目的地檢索，改為精確指向特定上下文。
- **符合架構**: 嚴格遵守「Admin 管理、User 消費」的 RBAC 設計原則。

## What (做什麼)

### 成功標準 (Success Criteria)
- [ ] `enduser-ui-fe` 的 API 層具備 `getKnowledgeItems` 功能。
- [ ] `TaskModal` UI 包含功能完整的知識庫選擇器。
- [ ] 只有具備 `MEMBER` 以上權限的使用者可以讀取知識列表。
- [ ] 任務建立後，`knowledge_source_ids` 已正確寫入 `archon_tasks` 的 metadata。

## All Needed Context (上下文)

### 文件與參考資料
- **`PRPs/Phase_4.1_AI_Developer_Implementation_Plan.md`**: 參考目前的開發流程。
- **`archon-ui-main/src/features/knowledge/hooks/useKnowledgeQueries.ts`**: 參考獲取知識列表的邏輯。

### 期望架構異動
```bash
enduser-ui-fe/
└── src/
    ├── services/
    │   └── api.ts                  # 修改：新增 getKnowledgeItems
    ├── components/
    │   └── KnowledgeSelector.tsx   # 新增：任務視窗內的選擇元件
    └── components/
        └── TaskModal.tsx           # 修改：整合選擇器
```

## Implementation Blueprint (實作藍圖)

### 任務清單 (Implementation Tasks)

```yaml
Task 1: BACKEND - RBAC 權限確認
  - 檔案: `python/src/server/api_routes/knowledge_api.py`
  - 行動: 確保 `GET /api/knowledge-items` 允許 `MEMBER` 角色進行 READ 操作。

Task 2: FRONTEND - API 客戶端更新
  - 檔案: `enduser-ui-fe/src/services/api.ts`
  - 行動: 實作 `getKnowledgeItems()`，僅抓取 ID 與標題等輕量資訊。

Task 3: FRONTEND - 選擇器元件實作
  - 檔案: `enduser-ui-fe/src/components/KnowledgeSelector.tsx`
  - 行動: 使用現有 UI 規範建立多選或單選選單，並具備過濾搜尋功能。

Task 4: FRONTEND - 任務視窗整合
  - 檔案: `enduser-ui-fe/src/components/TaskModal.tsx`
  - 行動: 將 `KnowledgeSelector` 加入表單，並在 `onSubmit` 時傳遞 `knowledge_source_ids`。
```

## Validation Loop (驗證)

1. **語法檢查**: `make lint` 確保符合前端規範。
2. **整合測試**: 
   - 在 Admin UI 上傳檔案。
   - 在 End-User UI 建立任務並嘗試選取該檔案。
   - 檢查資料庫 `archon_tasks` 表中的 `metadata` 是否包含正確的 ID。
