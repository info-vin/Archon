---
name: twin-simulator
description: 數位雙生模擬器與混沌 E2E 驗證技能。啟動百關微型場景矩陣驗證、注入網路混沌、執行實體像素級視覺排版比對，並呼叫視覺裁判進行 UI 版面公證，以確保極端邊界下的商業閉環健全。
---

# Digital Twin Simulator Skill (數位雙生模擬器驗證技能)

## Overview

本技能提供 Agent 使用 **數位雙生 (Digital Twin)** 與 **智慧型流程自動化 (IPA)** 進行 E2E 商業流程、權限防禦與極端環境驗證的規範。

透過宣告式關卡矩陣 (Campaigns A-D)、Playwright 路由攔截 (Chaos Injection) 以及實體截圖的 PIL 像素比對門禁，此技能可全自動在背景對 100+ 個關卡進行測試並回傳結算矩陣。

---

## 執行流程 (Workflow Instruction)

當您需要驗收特定人類角色工作流（如 Alice、Bob、Charlie 的操作鏈），或者需要驗證系統在慢速網路/伺服器錯誤下的穩定性時，請調用此 Skill：

### Step 1: 產生/重設動態關卡 YAML 腳本
* **指令**: `make twin-gen-levels`
* **說明**: 執行 `scripts/level_generator.py`，基於目前的角色（Alice, Bob, Charlie, DevBot）及權限配置，動態產生 100 個參數化關卡 YAML 腳本至 `scripts/twin_scenarios/05_generated_levels/` 下。

### Step 2: 執行模擬器全關卡闖關 (預設執行前幾關)
* **指令**: `make twin-simulator`
* **說明**: 啟動 `scripts/simulator_runner.py`。預設會啟用 `concurrency=3` 併發、`headless=true` 靜默執行，並限制執行前幾關以防超時。

### Step 3: 除錯與視覺回放單一關卡
* **指令**: `make twin-record SUBDIR=05_generated_levels SCENARIO=<Level_ID>`
* **說明**: 在背景啟動 Playwright 並啟用 `headless=false` 有頭視窗，執行特定的關卡 YAML，並在完成後自動產出 E2E webm 錄影與文字 metadata。

---

## 核心機制與自癒指引 (Core Mechanisms & Troubleshooting)

### 1. 混沌網路注入 (Chaos Network Injection)
* **機制**：在 `enable_chaos=True` 時，雙生執行器會攔截 `/api/marketing/**` 與 `/api/stats/**` 請求，有 **5% 機率模擬 HTTP 500 錯誤**，**50% 機率注入 1s-3s 延遲**。
* **排錯**：若關卡因 500 錯誤崩潰，請檢查前端 React 代碼是否未實作防禦性 Loading 狀態或 API Error boundary 導致白屏死鎖。

### 2. 實體視覺對比門檻 (Visual Diff Gate)
* **機制**：Runner 會將產出的截圖與 `.twin/baselines/` 下的基準圖進行逐像素對比。
* **分流處理**：
  * **差異度 <= 5%**：判定視覺無虞，靜默通過以節省 Token。
  * **差異度 > 5%**：自動喚醒 `scripts/vision_judge.py`（Gemini Vision），對畫面文字重疊、元件遮擋與頭像變色進行多模態 AI 評判。
* **自癒**：若版面改變（如新增了元件），請在確認無誤後將新截圖複製覆蓋 `.twin/baselines/` 的基準圖以更新 Baseline。

### 3. 沙盒錯峰資料庫隔離 (Sandbox Isolation)
* **機制**：執行前置 Hook 會呼叫 `setup_level_sandbox.py`。所有測試數據以 `level_id` 進行 row-level 隔離，並引入 random jitter 錯峰執行，防範多實例並發死鎖。
