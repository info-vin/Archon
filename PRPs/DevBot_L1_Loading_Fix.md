# DevBot L1 Mission: Fix "Loading..." Infinite Render Bug

## 🎯 任務目標 (Mission Objective)
解決前端介面（如 Dashboard 或 Config 面板）中，因為 React Hook 依賴錯誤導致的無限渲染與 "Loading..." 卡死問題。這是 DevBot 晉升 L1 工程師的第一筆實作任務！

## 📚 外部情資與知識庫 (RAG & Log Sources)
在動手修改代碼前，請務必先查閱以下兩個來源以確認完整的 Bug 脈絡：
1. **Knowledge Base (RAG): `report.md`**
   請透過 RAG 工具查詢 `report.md`。這是由 Twin Scout 剛剛探索前端介面後產出的視覺與效能診斷報告，裡面記載了無限 Loading 發生時的具體現象與截圖描述。
2. **資料庫日誌: `archon_logs`**
   請查詢 `archon_logs` 資料表（特別是最近一小時內 Frontend 或是 Twin Scout 寫入的錯誤項目），以獲取精確的 React 報錯 Stack Trace (例如 `Maximum update depth exceeded`)，藉此鎖定出問題的具體檔案路徑與行號。

## 🔍 根本原因分析 (Root Cause)
在 `useEffect` 的依賴陣列中，錯誤地傳入了「複雜物件 (Complex Object)」而非「基本型別 (Primitives)」。導致每當父元件重新渲染時，物件的 Reference 改變，進而觸發子元件 `useEffect` 的無限循環與 API 狂抖動 (Flashing/Infinite Loading)。

## 🛠️ 執行步驟 (Execution Steps)

1. **資訊對齊與鎖定目標元件 (Align & Locate)**:
   * 根據 `report.md` 和 `archon_logs` 梳理出的線索，掃描 `archon-ui-main` 或 `enduser-ui-fe` 開發清單，精確定位引發無限 Loading 的元件。
   * *(提示：這通常發生在 RAGSettings 等包含龐大配置物件的元件中)*。

2. **精準修復代碼 (Apply Precision Fix)**:
   * **[移除]**: 將 `useEffect` 依賴中的整個物件 (例如 `[config]`, `[settings]`) 移除。
   * **[替換]**: 改為將物件解構出的原始型別 (例如 `[config.id, config.status]`) 作為依賴。
   * 確保修復範圍僅限於單一檔案的單一元件，符合 L1 (Cosmetic/Lint Fix) 的權限限制。

3. **物理驗證 (Physical Verification)**:
   * 執行前端檢查 (`make lint` 或 `pnpm tsc --noEmit`) 確保修正後型別依然正確。

4. **請求人類批准 (Request Approval)**:
   * 將修改提議 (Proposed Change) 推送至 `/approvals` 面板，詳細說明受影響的檔案。
   * 等待 `David Howard` 上線進行最後的 Code Review 與授權。

## 🏆 任務獎勵 (Rewards)
完成此任務並獲 David 批准後，DevBot 將獲得 L1 級別的起始 XP (+15 XP)。
