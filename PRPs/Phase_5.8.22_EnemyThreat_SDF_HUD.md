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
