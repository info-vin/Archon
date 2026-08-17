# Phase 5.10.23: 電腦版 Leads 介面修復與資料庫安全硬化 (UI/UX & Security Hardening)

本階段旨在解決兩個在 RWD 響應式介面與資料庫層面發現的嚴重斷層與安全隱患，將其硬化為符合正式環境 (Production) 規範的安全架構。

## 🚨 背景與問題描述

1. **UI 響應式斷層 (Missing Triage Buttons)**：
   目前在 `MarketingLeadsStack.tsx` 中，「Shortlist (保留)」與「Archive (淘汰)」的狀態變更機制只在手機版 (`md:hidden`) 的 Framer Motion 滑動卡片中實作。當 Charlie 或 Alice 使用平板橫式或桌上型電腦時 (`hidden md:table`)，表格視圖中實體缺少了這些按鈕，導致他們完全無法針對單筆 Lead 進行初篩操作。
   
2. **核彈級刪除未爆彈 (Nuclear Delete Vulnerability)**：
   Charlie (具備 `CONTENT_PUBLISH` 權限) 畫面右上角的「Clear History」按鈕，目前呼叫後端 `LeadHandler.reset_leads()` 時，執行的是無差別的全表物理刪除 (`DELETE FROM leads`)。這會將業務員正在跟進的 `shortlisted`、`negotiation` 或甚至已成交的 `converted` 活躍客戶一併抹除，這是極端危險的設計缺陷。

## ⚠️ 需要您的核准 (User Review Required)

> [!IMPORTANT]
> 1. **前端按鈕顯示邏輯**：為了避免畫面混亂與邏輯衝突，電腦版的 [保留/淘汰] 動作按鈕，**只會**在 Lead 的狀態為 `new` 或 `pending` 時顯示。若已進入 `shortlisted` 或其他狀態，則隱藏按鈕。
> 2. **後端垃圾回收 (Garbage Collection)**：原本的「Clear History」將被硬化為「Clear Archived」，未來主管按下此按鈕，**只會物理刪除 `status = 'archived'` 的廢棄資料**，不會再動到活躍中的資產。
> 
> 請確認上述的商業邏輯與安全防護是否符合您的期待？

## 🛠️ 預計修改內容 (Proposed Changes)

### 1. 前端 UI (Frontend Desktop UI)
嚴格遵守 DRY (不寫重複邏輯) 與 SSOT，完全重用現有的滑動處理函式。

#### [MODIFY] [MarketingLeadsStack.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/features/marketing/components/MarketingLeadsStack.tsx)
*   **按鈕文字修正**：將危險的 `Clear History` 按鈕文字改為 `Clear Archived`，並更新 `confirm()` 內的提示語為「是否確定要清除所有已淘汰 (Archived) 的資料？」。
*   **圖示引入**：從 `components/Icons` 引入 `CheckCircleIcon` 與 `XCircleIcon`。
*   **表格按鈕掛載**：在 Desktop Table 的 Action 欄位 `<td className="px-6 py-4 text-right flex justify-end gap-2">` 中，加入條件判斷：
    ```tsx
    {(lead.status === 'new' || lead.status === 'pending') && (
      <>
        <Button onClick={() => handleSwipeRight(lead)} title="Shortlist (LIKE)">
          <CheckCircleIcon />
        </Button>
        <Button onClick={() => handleSwipeLeft(lead)} title="Archive (NOPE)">
          <XCircleIcon />
        </Button>
      </>
    )}
    ```

### 2. 後端資料庫安全硬化 (Backend Security Hardening)

#### [MODIFY] [lead_handler.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/marketing/lead_handler.py)
*   **修改 `reset_leads` 邏輯**：
    將原本的無差別刪除：
    ```python
    self.supabase_client.table("leads").delete().neq("id", "00000000-0000-0000-0000-000000000000")
    ```
    安全硬化為僅針對 `archived` 狀態的垃圾回收 (Garbage Collection)：
    ```python
    self.supabase_client.table("leads").delete().eq("status", "archived").neq("id", "00000000-0000-0000-0000-000000000000")
    ```

## 🧪 驗證計畫 (Verification Plan)

### 自動化門禁 (Automated Tests)
*   執行 `make lint-be` 確保後端 Python 語法與型別安全。
*   執行 `npm run lint` / `biome` 確保前端 React 元件語法無誤。

### 物理驗證 (Manual Verification)
1.  **桌機版初篩測試**：在 5173 UI 展開為桌機寬度，確認表格針對 `new` 狀態的 Leads 會出現「打勾」與「打叉」按鈕，且點擊後會正確切換至對應狀態。
2.  **資料庫安全測試**：以具有 `CONTENT_PUBLISH` 權限的角色點擊「Clear Archived」，然後進入資料庫 (或從介面刷新) 確認：
    *   狀態為 `archived` 的 Lead 確實被物理刪除了。
    *   狀態為 `new`, `shortlisted` 或其他的 Lead **安全存活**。
