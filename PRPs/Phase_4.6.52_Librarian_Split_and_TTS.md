# Phase 4.6.52: LibrarianService 分拆與語音合成 (TTS) 服務導入

> **目標 (Goal)**: 
> 1. **LibrarianService 解耦 (L2 模組化)**: 依據技術債盤點決策，將行數過長的 `LibrarianService` (450+ 行) 物理分拆為多個具備單一職責的模組，並提供 Facade 以保持向後相容。
> 2. **TTS 語音服務導入 (Text-to-Speech)**: 整合 `gemini-3.1-flash-tts-preview` 模型，為系統建立專屬的 `TextToSpeechService`，並考慮 Free Tier 的 API 限制。

---

## 1. 戰略與限制分析 (Strategy & Constraints)

### 1.1 TTS 模型額度分析 (gemini-3.1-flash-tts-preview)
根據最新調查，TTS Preview 模型適用於 Free Tier：
- **限速**: 預估約 10-15 RPM (Requests Per Minute)，250-500 RPD (Requests Per Day)。
- **Token 換算**: 音訊輸出約 25 tokens/秒。
- **架構決策**: 因為是 Preview 模型且限速嚴格，`TextToSpeechService` 必須具備 **非同步調用 (client.aio)** 與 **指數退避重試 (@retry_with_backoff)**，且不應阻斷主流程（Fire & Forget 或 Background Task）。

### 1.2 LibrarianService 拆分架構
將 `LibrarianService` 拆分至 `src/server/services/librarian/` 目錄：
- `web_archiver.py`: `archive_any_url`, `archive_web_research`
- `business_archiver.py`: `archive_sales_pitch`, `archive_style_critique`, `archive_failure_case`
- `file_archiver.py`: `archive_file`
- `librarian_facade.py`: 作為原有 `LibrarianService` 的進入點，負責將方法路由到上述模組。

---

## 2. 執行任務 (Implementation Tasks)

### 🧱 任務 1：LibrarianService 模組化
- [x] **Task 1.1**: 建立 `src/server/services/librarian/` 目錄與子檔案。
- [x] **Task 1.2**: 將爬蟲與網路研究邏輯遷移至 `web_archiver.py`。
- [x] **Task 1.3**: 將商業邏輯（Pitch, Critique, Failure Case）遷移至 `business_archiver.py`。
- [x] **Task 1.4**: 將檔案處理邏輯遷移至 `file_archiver.py`。
- [x] **Task 1.5**: 實作 `librarian_facade.py` 並替換原有的 `librarian_service.py`。
- [x] **驗證**: `make test-be` 必須 100% 通過，確保無向後相容性破壞。

### 🗣️ 任務 2：TextToSpeechService 開發
- [x] **Task 2.1**: 在 `src/server/services/` 下建立 `text_to_speech_service.py`。
- [x] **Task 2.2**: 實作非同步的 `generate_audio` 方法，呼叫 `gemini-3.1-flash-tts-preview`，並掛載 `@retry_with_backoff`。
- [x] **Task 2.3**: 實作 TTS 服務的單元測試，驗證其在 API 金鑰缺失或 429 錯誤時能優雅降級。

---

## 3. 驗證標準 (Definition of Done)

- [x] `LibrarianService` 原檔案被刪除，由 `librarian/` 資料夾取代。
- [x] `TextToSpeechService` 成功通過隔離測試。
- [x] 系統 `make lint`, `make test-be`, `make persona-audit` 全綠。