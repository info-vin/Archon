# Phase 5.8.4: 遊戲體驗與新手引導升級 (UX & Tutorial Enhancements)

> **核心原則：拒絕樂觀路徑 (No Happy Path) 與 物理對齊**
> 本階段嚴格禁止虛假開發與幻覺。任何語系切換、進度條綁定與教學資料替換，皆須完全依賴實體驗證與官方文件規範（如 TranslationServer 與 CSV 匯入機制）。卡牌擴充模組必須在 TDD 中確保 OCP (開閉原則) 的物理擴充性。

## 階段一：開場動畫 (Start Animation)
**門禁**：必須使用高相容性格式（`.ogv`），嚴禁直接塞入可能在 Web/Linux 導出時破圖的 `.mp4` 且不做錯誤處理。

*   **任務 1.1：影片格式轉碼與置入**
    *   將 5173 前端的 `hero_animation.mp4` 轉碼為 `.ogv` (Ogg Theora) 格式。
    *   放置於 `recontextualization/assets/videos/hero_animation.ogv`。
*   **任務 1.2：建立 `IntroVideo.tscn`**
    *   建立包含 `VideoStreamPlayer` 的場景，設定自動播放。
    *   實作任意鍵/滑鼠點擊跳過功能 (`_input` 攔截)。
    *   結束後自動轉跳 `GameBoard.tscn`。
*   **任務 1.3：`MainMenu.gd` 邏輯替換**
    *   玩家點擊「New Career」時，轉跳至 `IntroVideo.tscn` 而非直接進入主遊戲。

## 階段二：語系設定與遊戲內暫停選單 (Localization & Pause Menu)
**門禁**：嚴禁手寫 `if lang == "en"` 的硬編碼字串替換，必須使用 Godot 官方 `TranslationServer`。

*   **任務 2.1：建立 `translations.csv`**
    *   於 `recontextualization/locale/translations.csv` 建立標準鍵值表（包含 `keys`, `en`, `zh_TW`）。
    *   由 Godot 自動匯入生成 `.translation` 資源檔。
    *   將 `GameBoard` 與 `MainMenu` 的所有 Label 綁定對應 Key。
*   **任務 2.2：實作 `PauseMenu.tscn` (暫停選單)**
    *   建立獨立的暫停選單 UI，支援 ESC 鍵或點擊呼叫。
    *   包含：繼續遊戲 (Resume)、儲存進度 (Save)、讀取進度 (Load)、回主選單 (Quit to Menu)。
*   **任務 2.3：擴充 `SaveManager.gd` 與主選單設定**
    *   `SaveManager.gd` 新增 `language` (預設 `zh_TW`) 與 `bgm_volume`。
    *   在 `MainMenu.tscn` 新增語系下拉選單與音量滑桿，動態綁定 `TranslationServer.set_locale()` 與 `AudioServer`。

## 階段三：新手引導紅色呼吸框 (Tutorial UI Breathing Frame)
**門禁**：必須是可複用的疊加層，嚴禁在每個按鈕內部寫死閃爍邏輯。

*   **任務 3.1：建立 `FocusFrame.tscn`**
    *   使用 `Panel` 搭配 `StyleBoxFlat` (紅色邊框、內部透明)。
    *   內建 `Tween` 動畫，實現 `modulate:a` 的無限往復閃爍。
*   **任務 3.2：擴充 `TutorialManager.gd`**
    *   實作 `highlight_node(target_node_path: String)`，將 `FocusFrame` 動態疊加於目標節點上方，引導玩家操作。

## 階段四：HUD 白話文翻譯與「血條化」 (HUD Clarity & Progress Bars)
**門禁**：進度條顏色必須與卡牌晶片顏色達成 100% 物理一致性。

*   **任務 4.1：UI 血條化替換 (`GameBoard.tscn`)**
    *   **系統危機值 (Crisis HP)**：替換為紫色/暗紅色 `ProgressBar`。
    *   **資料純淨度 (Purity)**：替換為**綠色** `ProgressBar` (0~100%)，完美對應🟢黃金命中晶片。
    *   **投毒率 (Poisoning)**：替換為**紅色** `ProgressBar` (0~50%)，完美對應🔴紅幽靈雜訊晶片。
*   **任務 4.2：懸浮翻譯 (Tooltips) 注入**
    *   為所有的 HUD 元素設定 `tooltip_text`，特別是針對「投毒率」進行白話文解釋（系統資料被污染的機率）。

## 階段五：真實教學資料集 (Tutorial Built-in Dataset)
**門禁**：教學模式的檢索必須完全離線且具備確定性 (Deterministic)，嚴禁依賴外部網路。

*   **任務 5.1：建立 `tutorial_dataset.json`**
    *   於 `assets/data/` 放置一份包含 Godot 官方文件內容與雜訊的靜態 JSON 檔案。
*   **任務 5.2：`BackendClient.gd` 雙軌攔截**
    *   當 `GameState.is_tutorial_active == true` 時，攔截 HTTP 請求，改為讀取並解析 JSON，回傳固定且具教育意義的卡牌陣列。

## 階段六：卡牌擴充模組架構對齊與 TDD 更新 (Card Expansion Module Alignment)
**門禁**：禁止刪除既有的 AI Prompt，嚴格遵守 Maaack 擴充架構 (OCP)。

*   **任務 6.1：更新 `TDD_Recontextualization.md`**
    *   補回「卡片模組說明表 (Card Module Explanation Table)」。
    *   明確定義 5 種核心與擴充卡牌：Keyword, Dense, Reranker, Matryoshka, GraphRAG。
    *   標示這些卡牌在測試階段暫時對應的 `Maaack` 佔位圖示，並完整保留供未來使用的 `SDXL/Flux` 美術生成 Prompt。
