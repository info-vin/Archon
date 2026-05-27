---
name: twin-scout
description: 數位雙生 (Digital Twin) 整合驗證與模擬器技能。涵蓋「雙生對帳 (Twin Scout)」與「雙生模擬 (Twin Simulator)」，支援全角色流程公證、網路混沌注入、實體像素級視覺排版對比，確保系統在極端環境與動態演進下的功能與視覺自癒能力。
---

# Digital Twin Suite Skill (數位雙生整合驗證技能)

## Overview

本技能為 Archon 系統的**「數位雙生 (Digital Twin)」**核心品質驗證規範，將整個雙生驗證體系分為兩個互補維度：
1. **雙生對帳 (Twin Scout - Audit Mode)**：單向的「安全稽核員」，扮演不同角色在真實環境下巡檢，利用 Gemini 進行「真實資料與 UI 現狀」的一致性公證。
2. **雙生模擬 (Twin Simulator - Playthrough Mode)**：雙向的「時空沙盒模擬器」，在隔離的資料沙盒中併發運行 100+ 個微型關卡，並注入混沌網路與進行實體像素級對比。

---

## 核心指令與下法 (Makefile Standard Command)

根據您的驗證目的，選擇對應的雙生指令：

### 1. 雙生對帳 (Twin Scout - 稽核巡檢)
* **本機原生稽核**：
  ```bash
  make twin-scout-action
  ```
  *說明*: 逐一模擬全角色（Alice, Bob, Charlie, Admin, DevBot）登入，並對帳真實資料庫數據。
* **容器化對帳**：
  ```bash
  make twin-scout
  ```
  *說明*: 在 Docker 容器內以無密碼 keychain 繞過方式執行對帳。

### 2. 雙生模擬 (Twin Simulator - 應力驗證)
* **動態關卡產生**：
  ```bash
  make twin-gen-levels
  ```
  *說明*: 產生 100 個涵蓋權限對抗、慢速網路、500錯誤、多模態與一致性審計的 YAML 腳本。
* **百關併發混沌闖關**：
  ```bash
  make twin-simulator
  ```
  *說明*: 以 Concurrency = 3 併發執行產出的關卡，並隨機注入 Latency 與 HTTP 500。
* **單一關卡有頭除錯錄影**：
  ```bash
  make twin-record SUBDIR=05_generated_levels SCENARIO=<Level_ID>
  ```
  *說明*: 開啟有頭視窗，錄製操作過程並將 `.webm` 影片輸出至資源路徑。

---

## 核心機制與自癒 (Under the Hood & Self-Healing)

### 1. 網路混沌注入 (Chaos Injection)
* 當 `enable_chaos=True` 時，雙生執行器會隨機攔截 `/api/marketing/**` 與 `/api/stats/**` 請求：
  * **5% 機率**：回傳 `HTTP 500`（模擬服務器異常）。
  * **50% 機率**：延遲 `1.0s-3.0s`（模擬網路阻塞）。
* **排錯**：若測試在此崩潰，請引導前端開發者為對應 API 加上防重送、Loading 鎖定及 Error Boundary 降級防護。

### 2. 實體視覺對比門檻 (Visual Diff Gate)
* 腳本執行後會產出 `scenario_screenshot.png` 截圖，並與 `.twin/baselines/` 的基準圖進行 RGB 影像逐像素相減。
* **自癒與分流**：
  * **變更率 <= 5%**：判定為細微網頁渲染噪訊，直接通過。
  * **變更率 > 5%**：自動執行 `scripts/vision_judge.py`（Gemini Vision），讓 AI 當作眼睛審查有無「文字重疊、元件遮擋、頭像變色錯誤」。
  * **更新基準**：若為正常改版，將新截圖覆蓋 `.twin/baselines/` 的對應 baseline 圖片即可更新基準。

### 3. 沙盒錯峰資料庫隔離 (Sandbox Isolation)
* 關卡 Pre-hook `setup_level_sandbox.py` 在寫入測試數據時，會以 `level_id` 進行數據隔離。
* 併發啟動時加入隨機 `0.1s-0.5s` 的時間差 (Jitter)，防止 Supabase 連線池過載與 row-level 死鎖。
