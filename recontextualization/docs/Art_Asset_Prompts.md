# 🎨 Art Asset Prompts (已遷移)

> [!WARNING]
> 🚨 **此文件已作廢 (Deprecated)** 🚨
>
> 所有的 AI 繪圖提示詞 (Art Asset Prompts) 皆已全面遷移至資料庫 `archon_prompts` 資料表，以確保單一事實來源 (Single Source of Truth, SSOT) 並落實權限控管。

## 如何檢視與修改繪圖提示詞？

請前往 **EndUser UI (Port: 5173)** 的 **「系統設定」 -> 「AI 提示詞管理」** 頁面進行操作。
您可以在那裡過濾分類為 `ART_ASSET` 的提示詞，並進行無縫的複製、貼上與修改。

## 為什麼要遷移？
1. **防止改 A 壞 B**: 過去分散的 Markdown 管理無法與 Godot 或 Python 後端即時同步，容易產生資料斷層。
2. **Pydantic 強型別校驗**: 後端已經升級，強制規範 `PromptResponse` 的結構，避免虛假的測試與樂觀路徑。
3. **UX 統一**: 使用者現在能夠直接透過前端介面一鍵複製正向與負向提示詞，不再需要手動從 Markdown 中提取。

*(此文件保留作為歷史參照點，禁止在此處新增任何新的提示詞。)*

---

## 自動化美術處理腳本 (Automated Asset Processing)

在生成 AI 美術資源後，原始檔案必須經過安全壓縮裁切與資源綁定，才能無縫匯入 Godot 專案。我們已全面棄用外部的 Python 腳本，改為使用 Godot 原生的自動化腳本管線 (Native Godot CLI Tools)。

### 執行降轉腳本 (Asset Optimizer)
* **腳本位置**：`src/tools/AssetOptimizer.gd`
* **功能**：掃描 `assets/images/`，自動進行完美的中心正方裁切 (Center Crop)，並使用 Lanczos 演算法降採樣至各類別規定的解析度（如 512x512 或 256x256）。
* **執行規範**：
  請使用 Godot 的 Headless 模式執行：
  ```bash
  # 在 recontextualization 根目錄下執行
  godot --headless -s src/tools/AssetOptimizer.gd
  ```
* **注意**：絕不可使用粗糙的自動去背演算法。所有頭像與 UI 底框皆應保留原始背景，透過 Godot UI 系統的 `MarginContainer` 或 Shader 進行遮罩 (Masking)，以避免鋸齒毛邊。

### 自動生成卡牌資源 (Resource Generator)
* **腳本位置**：`src/tools/GenerateCardResources.gd`
* **功能**：當產出新的卡牌圖檔 (`action_*.png` 或 `chip_*.png`) 後，此腳本會自動掃描圖庫，若尚未建立過對應的 `.tres` 資源檔，則自動建立並完成綁定 (包含 id, 標題、卡牌型別與圖示位址)。避免手動新增資源的人為遺漏。
* **執行規範**：
  ```bash
  # 在 recontextualization 根目錄下執行
  godot --headless -s src/tools/GenerateCardResources.gd
  ```
