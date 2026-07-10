# Phase 5.8.16: MainMenu UI/UX Overhaul & Margin Architecture

## 1. 核心目標 (Core Objectives)
- 徹底根除 `MainMenu` 中所有可能導致遊戲崩潰的寫死路徑（例如錯誤的 `transition_scene`）。
- 捨棄原生廉價按鈕，升級為賽博龐克風格的 `TextureButton`，並與全遊戲 UI 語彙統一。
- 引入動態視覺：開場播放 `hero_animation.ogv` 隨後縮小並漸變為正式標題 **"RECONTEXTUALIZATION"**，打造極致沉浸的登入體驗。

## 2. 各模組重構細節 (Module Refactoring Details)

### 2.1 崩潰斷層修復 (Crash Prevention)
*   **路徑修正**：將 `MainMenuController.gd` 中的 `transition.tscn` 修正為實體存在的 `TransitionVideo.tscn`。
*   **信號解耦**：移除 `MainMenu.gd` 中所有依賴 `$VBoxContainer/NewCareerButton` 的硬編碼，改用 `@export` 開放至 Inspector 綁定，徹底確保 UI 層級異動時信號不中斷。

### 2.2 視覺與轉場特效 (Visual & Transition)
*   **多媒體整合**：在 `MainMenu.tscn` 根節點配置 `VideoStreamPlayer`，掛載 `assets/videos/hero_animation.ogv` 作為進場背景。
*   **時序動畫 (AnimationPlayer)**：
    1.  啟動遊戲時，畫面被全螢幕的 Hero Animation 佔據，UI 按鈕與標題隱藏（Alpha = 0）。
    2.  影片播放至尾聲（或特定觸發點），動畫引擎啟動。
    3.  影片畫面縮小、透明度降低；同時，巨大且科技感十足的 "RECONTEXTUALIZATION" 標題從虛無中浮現。
    4.  主選單的各個賽博龐克按鈕（使用 `card_frame_blank.png` 外框）依序展開。

### 2.3 UX 優化與在地化 (UX & Localization)
*   確保所有的按鈕（New Career, Continue, 等）皆具備正常的 Hover / Click 發光回饋，且綁定正確的 `translations.csv` 鍵值。
*   Settings 區塊（音量控制與語言下拉選單）同樣納入全新的玻璃面板或對齊網格中，不再隨意散落。

## 3. 驗收標準 (Acceptance Criteria)
1. **零崩潰保證**：點擊任何主要按鈕，皆能成功且順暢地跳轉至對應場景。
2. **動態演出公證**：啟動 `MainMenu` 必須能看到流暢的影片與 UI 淡入縮放轉場，拒絕死板跳接。
