# 🎯 物理鑑識報告與修復計畫：根除 LLM 同步阻塞斷層 (Async/Sync Boundary Fix)

## 📌 檢討與真相查明 (Autopsy & Root Cause Analysis)
指揮官，您的質疑如雷貫耳，完全命中要害！我先前的推論確實落入了「不看歷史、盲目發明」的虛假開發陷阱。

**針對您的兩個質疑，我已完成物理查證：**
1. **為何還是硬編碼？** 
   我提議的 `timeout=120.0` 確實違反了「禁止硬編碼」與 SSOT 原則。
2. **503 不是已經修復過了嗎？** 
   是的！查閱 `GEMINI.md` 的歷史紀錄，我們早在之前的 Phase (Ref: 04-02, 04-15, 04-20 等) 就已經「全面遷移至官方 Google `genai.Client`，解決 SDK 斷層導致的 503 錯誤與死迴圈」，SDK **早就內建了**完善的指數退避重試 (Exponential Backoff) 來處理 503。DLQ (Dead Letter Queue) 也早就實作於 `worker_service.py` 之中。

### 🚨 真正的元兇：非同步邊界的致命斷層 (The Real Gap)
既然 503 退避已經寫好了，為何排程器還會卡死 26 分鐘？我用 `grep` 徹底掃描了代碼庫，發現了真正的實體斷層：**有人在 `async def` (非同步) 的函式中，錯誤地呼叫了「同步 (Synchronous)」的 SDK 介面！**

在以下檔案中：
- `python/src/server/services/projects/tasks/ai_operations.py` (第 92 行)
- `python/src/server/services/marketing/visual_generator.py` (第 32 行)

這兩處使用了 `client.models.generate_content(...)` (同步版本) 而非 `await client.aio.models.generate_content(...)` (非同步版本)。
這導致當 Gemini 發生 503 需要進行內部指數退避重試時，SDK 觸發的是同步的 `time.sleep()`！這個同步睡眠直接**鎖死了 APScheduler 所在的 Async Event Loop 主執行緒**，造成排程器停擺長達 26 分鐘！

## ⚠️ User Review Required

> [!WARNING]
> **物理修復確認**：這一次我們不搞任何「虛假的新功能」，而是實實在在地把寫錯的 API 介面矯正。我們將把所有殘存的同步呼叫改為 `await client.aio.models...`，讓 SDK 在重試時能正確使用 `asyncio.sleep()` 讓出執行權，排程器就不會再被卡死了！請問您是否同意這個基於物理證據的修復計畫？

## 🛠️ Proposed Changes

### [MODIFY] `python/src/server/services/projects/tasks/ai_operations.py`
- 第 92 行：將同步的 `response = client.models.generate_content(...)` 替換為非同步的 `response = await client.aio.models.generate_content(...)`。

### [MODIFY] `python/src/server/services/marketing/visual_generator.py`
- 第 32 行：將同步的 `native_resp = client.models.generate_content(...)` 替換為非同步的 `native_resp = await client.aio.models.generate_content(...)`。

## 🔍 Verification Plan

> [!IMPORTANT]
> **靜態與型別公證 (Zero Fake Verification)**
> 1. 修復後，執行全域搜尋 `grep -rn "\.models\.generate_content" python/src/server/`，確保所有在 server 範圍內的呼叫皆已根除，僅剩下 `.aio.models.`。
> 2. 執行 `make lint-be` 與 `make test-be`，確保原本會卡死的 Live 測試能透過非同步機制優雅通過或被正確跳過。
