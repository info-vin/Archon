# Phase 5.9.30: Agent Server Decomposition & L2 Hardening

## 1. 核心目標 (Core Objectives)
- 將巨石架構 `python/src/agents/server.py` 拆解為 `FastAPI` 模組化的 Router (`routes/endpoints.py`, `routes/workflow.py`, `routes/health.py`)。
- 抽離 `lifespan.py` 與 `models.py`，降低單一檔案複雜度，杜絕 404 路由嵌套問題。
- 遵循 SSOT 原則與「Physical Mock 真實性」 (Rule #13)，在不改動單元測試簽章的前提下，移除與優化 `CredentialManager` 內部贅餘邏輯。

## 2. 變更範圍 (Scope of Changes)
- `python/src/agents/server.py` (簡化為 Router Entrypoint)
- `python/src/agents/routes/*` (新增路由模組)
- `python/src/agents/lifespan.py` (環境變數檢查與啟動週期)
- `python/src/agents/models.py` (共用 Pydantic Model)
- `python/src/server/services/credentials/manager.py` (重構但不破壞 5 個 Proxy 方法簽章)

## 3. Code Review 與架構反思 (Code Review & Architectural Reflections)
- **單一職責原則 (SRP)**: `server.py` 不再承擔路由處理細節，徹底回歸啟動與組裝職責，降低認知負擔。
- **Mock 真實性 (Rule #13)**: 我們曾試圖大規模消滅 `CredentialManager` 中的代理模式 (Proxy Wrappers)，但這會導致 44 項單元測試拋出 `AttributeError`。根據「物理對帳與假 Mock 預防」原則，我們選擇保留這 5 個 Wrapper 的簽章，以確保測試的行為與現實 100% 同步，同時保持 `manager.py` 檔案長度低於 400 行。
- **SSOT 防線**: 保留了 `lifespan.py` 中的 `[SSOT Violation]` 檢查，確保未經初始化的模型無法啟動，符合 Fail-Fast 精神。

## 4. 稽核與公證 (Audit & Certification)
- `make test-be`: 613 tests passed, 0 skipped/xfailed excluded, 0 failures.
- `uv run mypy src/agents`: Success, no issues found in 36 source files.
- `make phase-audit`: 四大架構與戰略子要塞健康度全數亮綠燈，Agent 引擎覆蓋率達 99.0%。

## 5. 下一步計畫 (Next Steps)
- 開始處理前端 `enduser-ui-fe` 的冗餘型別 (`ProjectAssignment`, `PermissionScope`) 清理，進行下一階段的瘦身任務。
