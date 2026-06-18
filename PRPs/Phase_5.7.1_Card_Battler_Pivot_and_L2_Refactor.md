# Phase 5.7.1: Card Battler Pivot, Rename, and L2 Refactoring

## 核心目標 (Goal)
本階段目標為優化原 `archon-card-battler` 遊戲專案的專案結構與可維護性。包含將冗長的專案資料夾更名為簡潔的單一單字，並將行數超出門檻（目前 MainUI.gd 已超標，後續預期 Main.gd 也將增長）的核心腳本進行 L2 模組化拆分，最終透過自動化測試與 UI 截圖物理公證來確保重構後的功能完全正常。

## 執行步驟 (Execution Plan)

### Step 1: 建立專屬開發分支 (Branching)
- **行動**: 建立並切換至新分支 `feature/phase5-7-1-card-battler-refactor`。
- **目的**: 確保改名與模組化過程在隔離的沙箱中進行，避免影響主幹的穩定性。

### Step 2: 專案更名與依賴修正 (Renaming & Dependency Fixes)
- **行動**:
  1. 將 `archon-card-battler` 目錄重新命名為使用者選定的單一名稱（例如 `deck` 或 `nexus`）。
  2. 使用全域搜尋替換前端文件 (`GamePage.tsx`) 與其他可能引用的開發腳本中的舊名稱字串。

### Step 3: L2 模組化重構 (L2 Modularization)
- **行動**:
  1. 鎖定目前的巨型檔案（如掃描報告指出的 `MainUI.gd`，以及預期會膨脹的 `Main.gd` 或 `GameState.gd`）。
  2. **實施拆分**: 將 UI 邏輯、動畫控制、訊號綁定（Signal Bindings）與核心商業邏輯物理分離。
     - 例如：將 `HUD` 相關邏輯抽出為 `HUDController.gd`。
     - 例如：將 `Card` 特效與拖曳邏輯抽出至單獨的 `CardInteraction.gd` 組件。
- **約束**: 確保拆分後，**沒有任何單一 `.gd` 檔案超過 400 行**。

### Step 4: 測試驅動驗證 (TDD Verification)
- **行動**: 執行在 `Phase 5.6` 奠定的 MiniTest 框架。
- **指令**: 透過命令列執行 Headless 測試。
- **目的**: 確保核心的「卡牌消耗」、「傷害計算」與「回合流轉」在 L2 拆分後依然能通過全部單元測試，無退化 (Regression)。

### Step 5: UI 截圖物理公證 (Visual Proof & Audit)
- **行動**:
  1. 撰寫或執行現有的 `capture_ui.gd` (或其他截圖腳本) 在 Godot 環境中自動載入主場景。
  2. 模擬一回合的卡牌打出動作。
  3. 擷取畫面並保存為 `proof_refactor_success.png`。
- **目的**: 遵守「物理穿透驗證」鐵律，透過視覺證據證明重構並未破壞任何 UI 錨點 (Anchors) 或渲染層級 (Z-Index)。

## 預期產出 (Deliverables)
- [ ] 乾淨的單一單字遊戲目錄。
- [ ] 所有 `.gd` 檔案均 < 400 行。
- [ ] 100% 通過的單元測試日誌。
- [ ] 一張證明 UI 渲染正常的公證截圖。
