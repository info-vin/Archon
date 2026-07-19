# Phase 5.8.22: Architectural Specification for Asymmetric Threat HUD (SDF Implementation)

## 1. Architectural Objective (架構目標)
本階段旨在基於 Signed Distance Fields (SDF) 渲染技術，建構與 Player Status HUD 具備同等抗鋸齒與幾何精準度之「敵方威脅狀態列 (Threat HUD)」。透過在片段著色器 (Fragment Shader) 層級實施座標軸鏡像反轉，系統能在零額外圖檔開銷下，達成完美的 1P vs 2P 非對稱視覺平衡，同時以高頻閃爍與光暈色彩偏移，具象化系統危機與高併發攻擊。

---

## 2. Visual-to-Data Mapping Specification (視覺與數據映射規範)
本模組嚴格綁定 `TDD_Recontextualization.md` 定義之三項核心威脅與一項全局限制。以下為具體的數據綁定與其視覺隱喻 (Visual Metaphor)：

1. **Poison Rate (資料投毒率) ➔ 【右側圓環 (Outer Ring)】**
   - **實作邏輯**：圓環填滿度 (Fill Ratio) 直接綁定 `poison_rate` (0.0 - 1.0)。
   - **材質表現**：採用 `#FF0055` (Crimson) 或 `#D4FF00` (Toxic Yellow) 作為主色，超過閾值時觸發高頻率的指數型光暈 (Exponential Bloom)。
   - **設計隱喻**：圓環的填充比例精準反映系統被感染的嚴重程度，宛如定時炸彈的倒數刻度，越滿越能帶來緊迫的危機感。

2. **Rate Limit (高併發限流警告) ➔ 【頂端動態標籤 (Top Label)】**
   - **實作邏輯**：綁定 API 請求狀態。常態顯示 `[ SYSTEM STABLE ]`；當接收到 429 或模擬限流時，強制覆寫為 `[ RATE LIMITED ]`。
   - **材質表現**：結合全域 Glitch Shader，觸發文字色差偏移 (Chromatic Aberration) 與 CRT 掃描線撕裂。
   - **設計隱喻**：作為最高優先級的警報燈，平日隱蔽，一旦遭受 DDoS 攻擊即以強烈的紅色故障視覺強制剝奪玩家注意力，呈現系統連線遭阻斷的真實絕望感。

3. **Crisis HP (系統危機總量) ➔ 【向左延伸之複合水平線 (Horizontal Multi-Bars)】**
   - **實作邏輯**：將單一 `Crisis_HP` 變數 (例如 10,000) 於視覺上正規化 (Normalize) 並等分為 3 個階段 (Phases)。玩家輸出傷害時，Shader 將依序由最上層的閾值向回扣減。
   - **設計隱喻**：打破單調的傳統長條，三條漸短的水平線象徵敵方防火牆的「三個防護層」或巨型 Boss 的多重結構。逐層擊破的視覺回饋能大幅提升打擊層次感。

4. **SLA Timer (服務級別協議倒數) ➔ 【底部幾何陣列 (Segmented Triangle Array)】**
   - **實作邏輯**：綁定 `EnvironmentManager` 之倒數計時器。每一個正三角形代表固定的時間區段 (Tick)，時間流逝時依序消除點亮狀態。
   - **設計隱喻**：以實體的「能量格」取代冰冷的數字，隨著三角形一格格熄滅，具象化任務剩餘時間的流逝，加深限時破關的致命壓迫感。

---

## 3. Shader Implementation Protocol (著色器實作協議)

### 3.1 座標軸鏡像反轉 (Coordinate Inversion)
為確保幾何渲染的對稱性，所有 UV 座標在進入 SDF 運算前，必須經過條件式翻轉：
```glsl
uniform bool is_mirrored = false;
void fragment() {
    vec2 uv = UV;
    if (is_mirrored) {
        uv.x = 1.0 - uv.x;
    }
    uv.x *= aspect_ratio;
    // 後續 SDF 運算完全共用...
}
```

### Core Objectives
- [x] Integrate `SciFiHUD.gdshader` into `PlayerStatusHUD` and `EnemyThreatHUD`.
- [x] Configure independent visual profiles:
  - Player: Cyan/Blue aesthetic, HP/AP bindings.
  - Enemy: Red/Crimson aesthetic, Threat/SLA bindings, Mirrored layout.
- [x] Decouple HUD logic from the core `MainUI` script to dedicated component scripts.
- [x] Overhaul Shader Geometry to "V11 Cyber-Vault" specifications:
  - 0.05 Heavy Armor Ring with exactly 0.25~0.75 monolithic cut opening.
  - 2x Thick Horizontal main beams paired with 0.8x dimmed thin diagonal linkages.
  - Monolithic seamless joint connecting the main frame directly into the ring core.
  - Ultra-thin decoupled internal HP bars with exact 0.1 border limit.
  - Mathematically precise text enclosures with bold fonts and optical pixel alignments.
- [x] Establish automated verification using headless viewport screenshots for both isolated HUDs and integrated GameBoard.

### 3.2 故障與干擾渲染 (Glitch & Interference Routines)
導入 `glitch_intensity` 參數，利用時間常數 `TIME` 進行正弦波擾動：
*   **UV 撕裂 (Tearing)**：`uv.x += sin(uv.y * 50.0 + TIME * 10.0) * glitch_intensity;`
*   **色散 (Chromatic Aberration)**：針對 R, G, B 通道進行微小且獨立的 UV 偏移採樣，強化系統遭入侵的視覺不安定感。

---

## 4. Component Hierarchy & Data Binding (組件層級與資料綁定)

*   **UI 節點分離**：
    所有文字 (Label) 必須掛載於 `ColorRect` 上層的 Control 節點中，絕不可參與 Shader 的 `is_mirrored` 反轉，確保文字的絕對銳利度與可讀性。
*   **全域對稱佈局 (GameHUD.tscn)**：
    採用 `HBoxContainer`，左側實體化 `PlayerStatusHUD`，中間配置 `Control (Size Flags: Expand)` 進行動態推擠，右側實體化 `EnemyThreatHUD`。
    - **對抗美學**：此佈局完美重現格鬥遊戲 (如快打旋風) 1P vs 2P 的競技對稱感，以左側冷澈的青藍色 (特務本錢) 對抗右側具侵略性的深紅色 (系統威脅)，建立極強的視覺張力。

## 5. Quality Assurance Criteria (品質保證門禁)
1. **抗鋸齒驗證 (Anti-Aliasing Check)**：所有斜切角必須通過 `smoothstep` 處理，禁止出現硬切邊緣。
2. **無損文字驗證 (Lossless Text Check)**：字體不可因 Shader 特效或縮放而產生模糊。
3. **效能驗證 (Performance Profile)**：SDF 與 Glitch 運算必須維持在極低的 Fragment Shader 開銷，確保無頭模式 (Headless) 測試與低階裝置下的 60FPS 流暢度。

---

## 6. Phase 5.8.x 總結與架構審查報告 (Architecture Analysis & Code Review)

### 6.1 Phase 5.8.x 時程與里程碑數據總覽
Phase 5.8.x 的核心主題為 **「Recontextualization（語意滲透與卡牌構築戰）」**。此階段將原本生硬的「工程後台／數位履歷表」前端介面，徹底重構為符合 Cyberpunk 世界觀的「卡牌戰鬥與駭客潛入」沉浸式 UI，同時對後端的 RAG 檢索邏輯進行了架構加固。

| 階段 | 核心目標／功能模組 | 關鍵交付物與實作內容 | 實體 Commit ID | 狀態 |
| :--- | :--- | :--- | :--- | :--- |
| **5.8.0** | RAG 牌組構築後端 | 開放 `/api/rag/hybrid-search` 路由、Supabase `hybrid_match_chunks` RPC、撰寫 `probe_rag_pipeline.py` 探針 | `76d1c446` | 🟢 已完成 |
| **5.8.1** | 核心邏輯移植 | 移植核心戰鬥實體與遊戲狀態變數，定義基礎數值 | `90de69dc` | 🟢 已完成 |
| **5.8.2** | 完整戰鬥循環實作 | 實現完整的 E2E 戰鬥迴圈（抽牌、出牌、棄牌與回合結束判定） | `90de69dc` | 🟢 已完成 |
| **5.8.3** | TDD 數學公式對齊 | 對齊戰鬥結算公式（AP 計算、資料純淨度 P、交付傷害 D）與單元測試斷言 | `bfb27995` | 🟢 已完成 |
| **5.8.4** | UX 與新手教學強化 | 實作 FocusFrame 聚焦框、教學狀態機 (Tutorial FSM) 以及本地模擬資料集 | `24becded` | 🟢 已完成 |
| **5.8.5** | MRL 與 GraphRAG 卡牌 (L5) | 支援 MRL 維度切片、Postgres 遞迴 CTE 圖搜尋 `/graph-search`、提交驗證探針 | `2c964af6` | 🟢 已完成 |
| **5.8.6** | 非線性 RPG 進度系統 | 實作 Clearance Ladder（權限天梯）與天賦樹修飾器數據模型 | `2c964af6` | 🟢 已完成 |
| **5.8.7** | 美術遷移與角色 UI | 套用透明卡牌、動態 Bezier 瞄準箭頭、扇形手牌排列、全域背景替換 | `e7245f4e` | 🟢 已完成 |
| **5.8.8** | 架構硬化與 L2 重構 | 抽出 `CombatJuice.gd` 與 `CardEffectResolver.gd`，確立 MVC 單向資料流 | `7808cacd` | 🟢 已完成 |
| **5.8.9** | 智能 RAG 特務編制 | 實作 3 人特務小隊限制、特務頭像預載、團隊算力與預算扣減數學模型 | `2d83dd0b` | 🟢 已完成 |
| **5.8.10**| 微控制器解耦重構 | 拆分並建立獨立視圖控制器（Dashboard, Workshop, MainMenu, GameBoard） | `8e64a272` | 🟢 已完成 |
| **5.8.11**| 硬編碼與斷層修復 | 全面拔除全域類別（帶有 `class_name`）的冗餘 `preload()` 字串路徑載入 | `9968a53a` | 🟢 已完成 |
| **5.8.12**| 動態 CardChip UI 與著色器 | 實作 `HexagonMask.gdshader` 六角形全像投影遮罩，修正卡牌容器邊距錨點 | `afe9b7ab` | 🟢 已完成 |
| **5.8.13**| 美術精細化與驗證修復 | 綁定過場影片、階級徽章，移除假圖片驗證，修復 UI 意外毀損技術債 | `fd6c9381` | 🟢 已完成 |
| **5.8.14**| 遊戲化 UI/UX 翻新 | 實作融合/分解雙模態、催化媒介插槽、商城導購發光、Line2D 環形矩陣線條 | `c1e910c4` | 🟢 已完成 |
| **5.8.15**| 全域實體對齊與幽靈淨化 | 徹底淨化 `SaveManager` 中的幽靈卡牌 ID，將命名空間統一為 `action_*` SSOT | `c9ba04ca` | 🟢 已完成 |
| **5.8.16**| 主選單翻新 | 整合轉檔後的 Intro 影片、音量與語言控制介面 | `8e64a272` | 🟢 已完成 |
| **5.8.17**| 3D 卡牌輪播選單 | 實作具備 3D 空間景深與圓周位移軌跡的 `CarouselContainer.gd` 輪播選單 | `50c86af9` | 🟢 已完成 |
| **5.8.18**| TDD 物理對齊 | 拔除 Enter 鍵檢索熱修復，強制使用拖拽行動卡觸發檢索，加入手牌上限 (5) | `d0aefa22` | 🟢 已完成 |
| **5.8.20**| 進階視覺打磨 | 微調滑鼠懸停縮放比、按鈕色差偏移、過場影片黑畫面死結修復 | `d0aefa22` | 🟢 已完成 |
| **5.8.21**| 玩家狀態 SDF HUD | 基於 SDF 幾何演算法與平滑抗鋸齒渲染的 V11 版「玩家狀態 HUD」 | `964ac227` | 🟢 已完成 |
| **5.8.22**| 敵方威脅 SDF HUD | 實作座標軸鏡像反轉的敵方狀態 HUD，Crimson 配色，SLA 三角形幾何陣列 | `9b8b494f` | 🟢 已完成 |

### 6.2 核心代碼審查與規範合規性報告
針對 `/recontextualization` 目錄下的實體 GDScript 程式碼，比對 `GEMINI.md` 與 `godot-4-audit` 的規範：
- **靜態型別與註解規範 (godot-4-audit 1.1 - 1.4)**：**100% 合規**。所有控制器與 View 腳本中的變數、函數參數及回傳值皆帶有明確的靜態型別宣告；信號連接全面使用 Callable 語法；已徹底重構移除了所有對宣告有 `class_name` 的全域類別的 `preload("res://...")` 載入。
- **Godot 4.x 無頭模式編譯防禦 (godot-4-audit 2.1)**：針對 `--headless` 在未經編輯器 GUI 掃描前 ClassDB 註冊表可能為空的引擎限制，程式碼在動態實例化內部測試工具與特殊策略結算器時，適當結合了防禦性的本地預載與型別檢查。
- **檔案行數門禁與 MVC 職責分離 (godot-4-audit 4.1)**：原本逐漸退化為「上帝類別」的 `GameBoard.gd` 與 `GameState.gd` 已完成模組化拆分。純視覺動畫特效剝離至 `CombatJuice.gd`；卡牌特技結算分支抽離至 `CardEffectResolver.gd`。

### 6.3 潛在技術債與反模式防禦清單
1. **SDF 著色器鏡像反轉的文字排版陷阱**：在 Fragment Shader 中使用了 `is_mirrored` 反轉 UV。**防禦要點**：所有文字 Label 必須掛載於 `ColorRect` 上層的 Control 節點中，絕對不可作為著色器反轉節點的子元件。
2. **Tween 非同步生命週期與記憶體洩漏**：主選單及場景切換動畫中，已全面使用 `call_deferred()` 或 Timer 安全接管場景跳轉。**防禦要點**：後續編寫任何帶有 `Tween` 的 UI 元件時，必須確保在 `_exit_tree()` 時手動調用 `tween.kill()`。
3. **SSOT Schema 與代碼命名的物理同步**：所有的卡牌 ID 已統一對齊為資料庫 SSOT 的 `action_keyword`、`action_dense` 與 `action_reranker`。**防禦要點**：若未來擴充或修改卡牌屬性，必須同步更新 Supabase RAG 表格、前端 API 映射、以及 GDScript 中的 `CardRegistry`。

### 6.4 當前狀態總結
- **當前 Git 狀態**：目前分支為 `feat/twins`，工作區乾淨。
- **自動化測試狀態**：Godot 無頭單元測試 (`MiniTest` 反射框架) 15 項 E2E 及單元測試全部通過 (`Passed: 15 / Failed: 0`)，無任何 Regression。
- **視覺公證**：視覺公證測試腳本與截圖工具運作正常，已產出物理圖檔供介面審查。本分析完全遵循「證據至上、物理對帳」原則。
