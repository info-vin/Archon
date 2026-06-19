# Phase 5.7.1: Card Battler Pivot, Rename, and L2 Refactoring

## 核心目標 (Goal)
本階段目標為優化原 `archon-card-battler` (現為 `arena`) 遊戲專案的專案結構與可維護性。根據最新 Code Review 掃描結果，目前雖然尚未有檔案超過 400 行門檻 (最大為 `MainUI.gd` 349 行)，但存在嚴重的「硬編碼」(Hardcoding) 問題（包含路徑、UI 尺寸與魔法數字）。本階段將進行 L2 模組化拆分、消除硬編碼、導入現代 Godot CI/CD，並最終透過自動化測試與 UI 截圖物理公證來確保功能完全正常。

## 執行步驟 (Execution Plan)

### Step 1: 建立專屬開發分支 (Branching)
- **行動**: 建立並切換至新分支 `feature/phase5-7-1-card-battler-refactor`。
- **目的**: 確保改名與模組化過程在隔離的沙箱中進行，避免影響主幹的穩定性。

### Step 2: 消除硬編碼與抽離設定檔 (Hardcoding Remediation)
- **行動**: 
  1. 盤點 `MainUI.gd`, `HelpOverlay.gd`, `DifficultyOverlay.gd`, `CardUI.gd`, `CombatVFX.gd` 內的魔法數字 (如字體大小 `font_size`, 元件尺寸 `Vector2(...)`, 延遲秒數等)。
  2. 移除 `MainUI.gd` 中直接使用 `preload` 或 `load` 載入 `res://` 路徑的寫法。
  3. 建立統一的 `GameConfig.gd` 或在節點上開放 `@export` 變數供 Inspector 注入，以利後續統一調整。

### Step 3: L2 模組化重構 (L2 Modularization)
- **行動**:
  1. 針對日漸膨脹的檔案 (如 `MainUI.gd`, `GameState.gd`) 提早進行預防性拆分。
  2. **實施拆分**: 將 UI 邏輯、動畫控制、訊號綁定（Signal Bindings）與核心商業邏輯物理分離。
     - 將 `HUD` 相關邏輯抽出為獨立 Controller。
     - 將 `Card` 特效與拖曳邏輯抽出至單獨的 `CardInteraction.gd` 組件。
- **約束**: 確保拆分後，**沒有任何單一 `.gd` 檔案超過 400 行**。

### Step 4: 測試驅動驗證與 CI/CD 導入 (TDD Verification & CI/CD)
- **行動**:
  1. 執行在 `Phase 5.6` 奠定的 MiniTest 框架驗證核心邏輯。
  2. 導入現代化的 Github Actions 流程。根據 2025 年的 Best Practice，採用 `chickensoft-games/setup-godot` 進行 Godot 引擎配置，並以 Headless 模式執行 `GUT (Godot Unit Test)`。
- **指令**: 透過命令列執行 Headless 測試。
- **目的**: 確保核心的「卡牌消耗」、「傷害計算」與「回合流轉」在 L2 拆分後無退化 (Regression)，並具備雲端自動化公證能力。

### Step 5: UI 截圖物理公證 (Visual Proof & Audit)
- **行動**:
  1. 撰寫或執行現有的 `capture_ui.gd` (或其他截圖腳本) 在 Godot 環境中自動載入主場景。
  2. 模擬一回合的卡牌打出動作。
  3. 擷取畫面並保存為 `proof_refactor_success.png`。
- **目的**: 遵守「物理穿透驗證」鐵律，透過視覺證據證明重構並未破壞任何 UI 錨點 (Anchors) 或渲染層級 (Z-Index)。

## 預期產出 (Deliverables)
- [x] 乾淨的單一單字遊戲目錄。
- [x] 所有 `.gd` 檔案均 < 400 行。
- [x] 將路徑、UI 尺寸與魔法數字從主腳本中剝離。 (`GameConfig.tres` 實作完畢)
- [x] 導入 Github Actions CI 流程 (`chickensoft-games/setup-godot` 搭配自製 `HeadlessRunner.gd` 實作完畢)
- [x] 100% 通過的單元測試日誌。
- [x] 一張證明 UI 渲染正常的公證截圖。

## ⚠️ 潛在技術債追蹤 (Tech Debt Backlog)
1. **MainUI.gd & GameState.gd 上帝類別風險 (God Class Risk) [已於 Phase 5.7.1 解決]**：
   - **完成狀態**：已成功實施 L2 視圖與邏輯解耦，抽離出 `CombatJuice.gd`（視覺特效與音效）、`DeckController.gd`（牌組載入）、`CardEffectResolver.gd`（卡牌技能效果解耦）與 `GitTranslator.gd`（動態翻譯）。`MainUI.gd` 降低至 304 行，`GameState.gd` 降低至 281 行，結構非常單一且職責分離。已通過全部 76 項單元測試與 UI 截圖物理公證。
   - **後續防禦**：持續監控所有核心主腳本，確保單一檔案行數在後續疊代中不超過 400 行門檻。
