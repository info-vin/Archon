# Phase 5.4.2: 數位雙生模擬器與百關微型場景自動化驗證架構 (Digital Twin Simulator & 100+ Micro-Scenario Automation Architecture)

## 1. 執行摘要 (Executive Summary)
本階段計畫將現有的「靜態 E2E 腳本驗證」升級為**「數位雙生動態模擬器 (Digital Twin Simulator)」**架構。
本計畫結合遊戲開發商的關卡驗證與自動化回放設計，定義了宣告式關卡模板，並規劃了 100+ 個微型測試關卡矩陣，以全面覆蓋角色權限邊界、異常網路、多模態輸入與資料一致性等極端邊界條件。

---

## 2. 遊戲開發商規格：宣告式關卡驗證模板 (Declarative Level Verification Template)
為確保測試的高維護性與低耦合度，定義以下標準的關卡宣告式規格模板：

```yaml
# =========================================================================
# ARCHON SIMULATOR LEVEL TEMPLATE (數位雙生關卡宣告式模板)
# =========================================================================
name: "L1_STAGE_04_RBAC_REJECTION_LOOP"        # 關卡識別碼 (Level ID)
mode: "scenario"                               # 執行模式 (scenario/audit/regression)
difficulty: "medium"                           # 關卡複雜度 (easy/medium/hard)
description: "Verify Charlie's approval review flow, AI recommendation, and state fallback."

# 1. 關卡前置條件自癒與資料隔離 (Stateful Sandbox Setup)
hooks:
  before_auth:
    - type: "python_function"
      module: "scripts.setup_level_sandbox"
      function: "initialize_state"
      args:
        level_id: "L1_04"
        force_clean: true

# 2. 玩家身分認證 (Persona Authentication)
auth:
  url: "/#/auth"
  user: "charlie@archon.com"
  password_env: "CHARLIE_PASSWORD"             # 安全變數，或 fallback 至預設密碼

# 3. 遊戲畫面解析度固定 (防止 UI 元素因解析度 RWD 跑版產生 False Negatives)
resolution:
  width: 1280
  height: 720

# 4. 關卡操作步驟 (Playthrough Steps)
steps:
  - action: "goto"
    url: "/#/nexus"
    wait_until: "domcontentloaded"
    timeout: 30000

  - action: "click"
    selector: "span:has-text('Op Load')"
    wait_selector: "div.content-review-panel"  # 物理對帳：點擊後必須看見目標面板
    timeout: 10000

  - action: "click"
    selector: "h4:has-text('Charlie Verification Blog Post')"
    wait_selector: "button:has-text('RETURN')"
    timeout: 10000

  - action: "click"
    selector: "button:has-text('Suggest with AI')"
    sleep_after: 2000                          # 給予非同步渲染緩衝時間

  - action: "click"
    selector: "button:has-text('CONFIRM RETURN')"
    timeout: 10000

# 5. 關卡結算公證 (Post-Playthrough Audit)
analysis:
  type: "static"                               # 靜態對帳 (static) 或 視覺評判 (visual_judge)
  screenshot: true                             # 結算時是否截圖交由 LLM Judge
  success_message: "WORKFLOW_SUCCESS"          # 成功簽證
  cleanup_on_success: true                     # 成功後是否自動釋放/還原資料庫垃圾
```

---

## 3. 100+ 個微型測試關卡矩陣設計 (100+ Micro-Scenario Matrix)
模擬器將透過 **「參數化矩陣關卡設計 (Parameterized Matrix Levels)」**，將 100 個小關卡拆解為四大主線任務 (Campaigns) 進行全自動執行：

```text
100+ Micro-Scenarios Matrix
├── Campaign A: 權限邊界對抗防禦 (40 關)
│   ├── Level A1-A20: 負面測試 (Negative Testing)。使用不同非 Admin 角色的 Token 請求敏感 API，驗證 100% 物理回傳 HTTP 403。
│   └── Level A21-A40: 權限動態生效。管理員變更權限後，前端 Token 與 Rerender 即時自癒。
├── Campaign B: 異常網路與 503 應力測試 (30 關)
│   ├── Level B1-B15: SSE 斷線重連。模擬 EventSource 隨機中斷，驗證 UI 無 Flashing (慢速/閃爍) 或重複 Request。
│   └── Level B16-B30: 慢速網路 (3G Mock)。驗證按鈕點擊後立即 disabled 鎖定，防 Double-click。
├── Campaign C: 多模態輸入邊界 (20 關)
│   └── Level C1-C20: 語音上傳異常（超長音檔、空白、多國混雜、GPS 遺失），驗證 AI 摘要與錯誤提示。
└── Campaign D: 商業數據一致性審計 (10 關)
    └── Level D1-D10: ROI 與 Token 統計。驗證跑完 E2E 後統計報表數據是否精準 +1。
```

---

## 4. 全面自動化驗證現況與優化方向 (Current Status & Automation Improvements)
經網路資料與軟體工程實務查證，目前的數位雙生測試已完成**「高價值骨幹的自動化閉環」**（Playwright 攔截 + 預置資料庫 Hook + WebM 自動錄影錄製），但離「全面自動化防禦」還有兩大關鍵斷層需要優化：

1. **UI 視覺與佈局斷層 (Visual Regression Gate)**：
   * *隱患*：靜態對帳僅驗證 DOM 節點，若按鈕被遮擋或透明化（DOM 依然存在），靜態測試無法察覺。
   * *優化*：未來應引入 `visual_judge.py` 進行截圖對照，交由 Gemini Vision 模組進行真實視覺排版、对比度與遮擋校驗。
2. **狀態空間爆炸 (State Space Explosion)**：
   * *隱患*：常規 E2E 僅能覆蓋快樂路徑，無法驗證高併發或異常中止時的灰色地帶。
   * *優化*：引入**「混沌測試 (Chaos Testing) 模擬器」**，在執行期間隨機注入斷網、重整與重複點擊，確保極端干擾下的自癒能力。

---

## 5. 實作計畫 (Implementation Plan)

為逐步落地上述優化方向並完成百關測試，規劃以下三階段實作方案：

### 階段一：矩陣關卡自動產生器與自動化執行器 (Matrix Level Generator & Runner)
* **目標**：實現動態產生與批次運行 100+ 個微型測試關卡，產出「關卡通過矩陣表」。
* **工作項目**：
  1. **實作 `scripts/level_generator.py`**：採用範本渲染引擎 (Jinja2)，讀取關卡矩陣設定檔 (JSON/YAML)，動態產生 100+ 個參數化測試場景。
  2. **實作 `scripts/simulator_runner.py`**：擴充現有 `twin_scout.py` 的 YAML 執行邏輯，支援併發關卡執行限制 (Concurrency Cap = 5)，防止機器過載。
  3. **產出 Dashboard 結算報告**：在 `scripts/` 下新增一個報告彙整工具，執行完畢後自動輸出 HTML / Markdown 格式的關卡通過報告。

### 階段二：AI 視覺裁判整合 (Visual Judge Integration)
* **目標**：引入 `visual_judge.py` 對複雜 UI（如 HUD 折線圖、彈出視窗遮擋）進行佈局與對比度校驗，解除「DOM 在但按鈕點不到」的盲區。
* **工作項目**：
  1. **擴充 `YAMLScenarioRunner`**：當 `analysis.type` 為 `visual_judge` 時，自動擷取 Playwright 完工後的 Full-page 截圖。
  2. **調用 `visual_judge.py` 核心服務**：將截圖、DOM Context 以及 AI 視覺檢查 Prompt 送入 Gemini API，回傳視覺布局合規性簽證。
  3. **整合 Visual Diff 門檻**：基於像素比對法 (Pixelmatch) 進行預篩，當像素變更率大於 5% 時才觸發 LLM-Judge 進行細緻語義評判，以節省 API Token 費用。

### 階段三：混沌工程模擬器 (Chaos Testing Simulator)
* **目標**：在 UI 執行期間，隨機注入非同步異常，硬化系統的韌性。
* **工作項目**：
  1. **實作 Playwright 網路混沌注入**：在 `simulator_runner.py` 中，針對指定比例 (e.g., 5%) 的 API 請求，隨機注入 2000ms - 5000ms 的延遲 (Latency Mock) 或隨機返回 HTTP 500/503。
  2. **UI 隨機干擾 (Chaos Monkey Event)**：在 Playwright 執行 Steps 的空檔中，有 10% 機率隨機觸發 `page.reload()` 或隨機發送點擊事件，驗證前端狀態機 (State Machine) 是否會鎖死或陷入無窮載入。

