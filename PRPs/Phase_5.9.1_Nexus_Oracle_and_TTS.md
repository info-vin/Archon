# Phase 5.9.1: Nexus Oracle 整合與 TTS 語音戰情摘要

## 🎯 階段目標 (Phase Goal)
將本週報表系統升級，導入 Nexus Oracle 戰略分析，並透過 TTS (Text-to-Speech) 產生音訊廣播，提升報表的吸收效率與價值。

## 📝 實作細節 (Implementation Details)

- `[x]` **Nexus Oracle 戰略注入**: 
  - 在 `report_service.py` 中，於產生週報總結前，先觸發 `NexusOracleAgent`，分析系統健康度、瓶頸與趨勢。
  - 將 Nexus Oracle 的洞見注入到最終的報表 Prompt 中，確保高管摘要不僅包含數據，還具備戰略指導意義。
  
- `[x]` **TTS 廣播整合 (Podcast Generation)**: 
  - 實作 `Librarian_TTS` 整合至 `report_service.py`。
  - 將產生好的週報文字，透過 `beta_graph` 的 `text_to_speech_service` 轉換為廣播音檔 (Podcast)。
  - 在最終的工作任務描述 (Task Description) 中附加音檔下載連結，提供聽覺化的戰情摘要。
  - **架構硬化**: 導入 Pydantic `TTSConfig` 作為單一事實來源 (SSOT)，消除硬編碼的 `TTS_TRUNCATION_LIMIT` (預設 4000)，確保配置型別安全。

## 🛡️ 驗證與公證 (Verification)
- `[x]` 透過自動化測試驗證 `NexusOracleAgent` 與 TTS 服務的回呼流程。
- `[x]` 確保排程不會因單點服務失敗而全面崩潰 (Resilience)。
