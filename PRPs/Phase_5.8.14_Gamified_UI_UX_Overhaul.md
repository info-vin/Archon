# Phase 5.8.14: Gamified UI/UX Overhaul & Margin Architecture

## 1. 核心目標 (Core Objectives)
- 將原有的「工程後台 / 數位履歷表」介面，徹底重構為符合 Cyberpunk 世界觀的「卡牌戰鬥與駭客潛入」沉浸式 UI。
- 落實遊戲經濟模型 (Margin)：包括 Token 預算限制、卡牌升降級機率，以及商城催化劑機制。
- 達成 100% 物理公證 (Headless Screenshot & TestHubUX 驗證)。

## 2. 各模組重構細節 (Module Refactoring Details)

### 2.1 隊友管理 -> 特務編制中心 (Teammate Dashboard)
*   **視覺重建**：移除底部導航列，加入玻璃擬物化 (Glassmorphism) `PanelContainer` 分隔左右版面。
*   **編制系統**：實作至多 3 人的多選機制 (Max 3 Squad)。
*   **Token 預算 (Margin)**：導入隊伍算力上限 (例如 10 Token)。每位特務依據等級 (Rank C/B/A/S) 消耗對應 Token。超過預算則拒絕編入並閃爍紅光警告。
*   **所見即所得情報**：放棄 Hover 懸停，右側直接顯示該特務的「引擎特性」與「基礎體力/算力」。
*   **真實素材**：替換假資料，使用 `avatar_alice.png`, `avatar_bob.png`, `avatar_charlie.png` 等真實測試頭像。

### 2.2 知識庫搜尋 -> 牌組構築矩陣 (Deck Management)
*   **3 卡武裝限制**：上方 (Equipped) 嚴格限制為 3 個插槽，並顯示總 Cost，此 Cost 必須受限於上方設定的特務 Token 總量。
*   **預組卡牌質感**：下方 (Available) 提供至少 6 張以上具備不同等級、類型與 Cost 的真實預組卡牌，取代白板佔位圖。
*   **純淨介面**：移除殘留的雙語標題與底部導航，正名為「核心武裝」與「備用記憶體」。

### 2.3 資料處理 -> 卡牌工坊 (Card Workshop)
*   **雙模態切換**：新增 **[ 融合 (Synthesis) ] / [ 分解 (Dismantle) ]** 頂部科技感 Toggle。
*   **機率與升降級矩陣**：
    *   **融合 (Upgrade)**：3 張低階卡合成 1 張高階卡，顯示升級成功率。
    *   **分解 (Downgrade)**：1 張卡降級拆解為 2 張低階卡/碎片。
*   **商城催化劑 (Catalyst Margin)**：矩陣核心放置「催化媒介」插槽，為空時顯示「前往商城獲取 (Go to Store)」發光提示，引導付費提升機率。
*   **高質感環形陣列**：使用 `bg_synthesizer.png` 或 `bg_vector_grid.png` 為底板，以 `Line2D` 發光線條與絕對座標，繪製真實的環形能量矩陣。取代巨型 Godot 按鈕，改用全像投影「執行 (EXECUTE)」面板。
*   **串接既有動畫**：確保執行時正確呼叫原本設計好的機率成敗動畫（成功高光、失敗震動碎裂）。

### 2.4 使用者設定檔 -> 駭客球員卡 (Character Dashboard)
*   **視覺主體重塑 (Player Card)**：廢除左右對半分割的履歷表排版。在畫面中心放置一張極具魄力的**「全像投影特務卡」**，帶有 3D 視差傾斜特效。數值（突破、隱匿、算力）直接刻印在卡面之上，如同高質感的 FIFA 球員卡。
*   **鑲嵌式天賦網 (Socketed Topology)**：天賦與模組不再是一張巨大的蜘蛛網，而是化為發光插槽，環繞、鑲嵌於特務卡周邊，並維持 `Line2D` 雷射連線。
*   **懸浮終端機 (Floating Terminal)**：點擊插槽時，伴隨 Glitch 雜訊彈出懸浮視窗，以打字機特效印出科幻 Lore，取代原本死板的右側文字區塊。

## 3. 結構化自動公證 (Automated Verification)
遵照「UX 驗證不能靠人工」的鐵律，本階段的 UI 重構必須伴隨 `TestHubUX.gd` 的物理斷言更新。所有驗證必須在 Headless 模式下 100% 通過：

### 3.1 控制項滅絕斷言 (Anti-Pattern Assertion)
*   **斷言目標**：遍歷所有四個場景，斷言絕對不存在 `ItemList`, `OptionButton`, `HSlider` 等原生廉價控制項。
*   **語言斷言**：利用腳本掃描所有 `Label` 與 `RichTextLabel` 的 `text` 屬性，斷言禁止出現特定的英文字串（如 Input 1, Output, Catalyst, SYNTHESIZE），確保 100% 在地化。

### 3.2 邏輯與拓樸斷言 (Structural & Logic Assertion)
*   **牌組與隊友斷言**：實例化 (Instantiate) 場景後，透過腳本強行塞入 4 張裝備卡或 4 名隊友，斷言 UI 邏輯會正確攔截並回傳錯誤 (強制 3 人/3卡 上限)。
*   **工坊雙模態斷言**：斷言 `CardWorkshop.tscn` 內必定存在 `SynthesisMode` 與 `DismantleMode` 兩個獨立的容器，且中心必須擁有 `CatalystSlot`。
*   **球員卡與雷射連線斷言**：斷言 `CharacterDashboard.tscn` 中不再含有 `GridContainer` 履歷表，且場景樹中必須包含 `Line2D` 節點（雷射射線）與具備打字機邏輯的 `RichTextLabel`（懸浮終端機）。

## 4. 驗收標準 (Acceptance Criteria)
1.  **公證通過**：嚴格執行 `GODOT_DISABLE_LEAK_CHECKS=1 /Applications/Godot.app/Contents/MacOS/Godot --headless -s Tests/TestHubUX.gd`，上述所有 `MiniTest` 自動化斷言皆必須回報 `PASS`，絕不允許靜默報錯或跳過。
2.  **視覺覆核 (嚴禁幽靈代碼)**：由 `Tests/Screenshotter.gd` (帶 GUI) 物理產出的四張新截圖，必須**親自審查**其內容確實包含 Line2D 連線、Hacker Player Card、Glitch Terminal 與 3進1 矩陣等，徹底符合本 PRP 的高品質要求。絕不允許未經審查就矇騙過關。

## 5. 核心崩潰修復與物理重構 (Null Instance Fix & Physical Refactoring)
*   **問題**: `CardSlot.gd` 的 `setup()` 在 `@onready` 尚未觸發時呼叫導致 Null Instance，連帶引發 `Screenshotter` 與 `CharacterDashboard` 星狀拓樸的毀滅性崩潰。
*   **修復**: 
    1. 在 `CardManagementMenu.gd` 與 `CardWorkshop.gd` 中，必須先執行 `add_child()` 再呼叫 `setup()`。
    2. 使用 `Line2D` 實作 `CardWorkshop` 的融合 (3進1) 與分解 (1進2) 真實射線排版，不再只是空殼 Button。
    3. 在 `CharacterDashboard` 中真正解放 `TopologyPanel`，繪製環繞特務卡面的實體發光插槽與星狀拓樸網。

## 6. 最新開發進度 (Progress Updates)
*   **Tab 1: 駭客檔案 (Character Dashboard) UI 極致微調完成**：
    *   完成終端機防變形切圖 (NinePatchRect 邊距擴展至 60px)，解決比例扭曲問題，並加上了 0.4 半透明玻璃背板內縮。
    *   完成 Avatar 圖層反轉與 HexagonMask Shader (`taper_amount = 0.25`)，套用著色器數學演算法切出完美的六角形實體頭像，完美鑲嵌於金屬套圖內。
    *   精確對齊標題與神經經驗值 (100 XP)，完美歸位 C 級節點行者勳章。
*   **【未來擴充備註】天賦拓樸互動**: 目前右側星盤拓樸的綠色/紅色天賦節點仍為靜態圖像。若未來需要實作如 ComfyUI 般的自由排版與即時連線功能，**【需要新增 拖曳.gd (Draggable Script)】** 來專門處理節點的滑鼠拖曳與 `Line2D` 即時重繪邏輯。
*   **Tab 2: 卡牌管理 (Card Management Menu) 3D 輪播與在地化重構完成**:
    *   **3D 圓形輪播 (Carousel)**: 捨棄生硬的原生佈局，導入自定義 `CarouselContainer.gd` 實作真正的 Z 軸深度、3D 縮放與圓周位移軌跡。
    *   **動態容積壓縮 (Dynamic Volume Compression)**: 若卡牌超過 6 張，系統自動將背景卡牌 (`min_scale`) 壓縮至 0.6x 倍率，前方焦點卡牌維持 1.05x，以10% 的完美重疊率營造厚實的牌組感，同時保障易讀性。
    *   **拖曳與即時試算**: 支援跨庫存拖曳裝備，自動踢除機制（上限 3 張），並即時動態加總算力負載、上傳速率、CDR 等戰力數值。
    *   **全面去硬編碼與中文化**: 導入 `translations.csv` 字典庫與 `tr()` 動態注入。徹底解決 UI 文字「中英混雜」與「時序渲染 `%d` 外露」的底層架構 Bug。
