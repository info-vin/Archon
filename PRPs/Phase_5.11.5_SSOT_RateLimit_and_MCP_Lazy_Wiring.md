# 系統架構重構計畫：SSOT 限流自適應與 MCP 延遲初始化

## 核心目標 (Goal Description)
1. **SSOT 限流重構**：解決 `rate_limiter.py` 中的硬編碼限速數值，將物理限速屬性統一收攏至單一事實來源 `model_ssot.py`，讓系統能自動感知 `DEFAULT_PRO` 為 Lite 模型並釋放 15 RPM 的真實效能。
2. **MCP 冷啟動自癒**：實作 `lazy_` 架構模式，將 MCP 的神經連線 (`list_tools`) 從 FastAPI 的 `lifespan` 阻塞階段中剝離，改由 `asyncio.create_task` 於背景無限制重試，徹底解決極端冷啟動環境 (如 Hugging Face) 下的 504 Gateway Timeout 與帶病啟動問題。

## User Review Required
> [!IMPORTANT]
> 此計畫嚴格遵循「不改 A 壞 B」與「拒絕虛假驗證」原則。
> 1. 我們不會修改目前散落在各模組呼叫 `wait_for_capacity(tier="pro")` 的代碼，而是透過底層動態攔截 (Interceptor Pattern) 覆寫。
> 2. `lazy_` 啟動設計只會剝離 MCP 的連線，原有的 Scheduler 與 Crawler 仍維持第一時間啟動，絕不會影響目前的週期排程作業。

## Proposed Changes

---
### 1. 模型限流 SSOT 集中化 (Model Rate Limit SSOT)

我們將在 `model_ssot.py` 中新增限流映射常數與動態解析方法，消滅硬編碼。

#### [MODIFY] [model_ssot.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/config/model_ssot.py)
- **新增常數**: `MODEL_TIER_DELAYS = {"lite": 4.5, "pro": 32.0, "embedding": 0.5}`
- **新增函數**: `get_delay_for_model(model_name: str) -> float`。透過解析實際的模型名稱字串（如 `gemini-3.5-flash-lite`），回傳真實的物理延遲（例如 4.5 秒）。

---
### 2. 限流器自適應重構 (Rate Limiter Adaptive Refactoring)

修改全域限流器，使其能夠「拆開包裝紙看內容」，不再死板依賴呼叫端的 Tier 名稱。

#### [MODIFY] [rate_limiter.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/system/rate_limiter.py)
- 移除硬編碼的 `_tier_delays = {"pro": 32.0, "lite": 4.5}`。
- 於 `wait_for_capacity` 內部，動態讀取 `model_ssot.py` 取得當前真實啟用的模型名稱，並調用 `get_delay_for_model`。
- **預期效果**：當排程呼叫 `wait_for_capacity(tier="pro")` 時，因為底層指向的是 `gemini-3.5-flash-lite`，系統會自適應採用 4.5 秒等待，直接將效能提升 7 倍。

---
### 3. MCP 連線生命週期解耦 (MCP Lifespan Decoupling)

將阻塞式的重試迴圈抽離為主線程外的獨立背景任務。

#### [MODIFY] [lifespan.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/core/lifespan.py)
- 移除原本 15 次 x 2.0s 且會拋出日誌的阻塞 `for` 迴圈。
- 新增非同步函數 `lazy_mcp_neural_wiring()`，使用 `while True` 與 `try-except` 包覆 `mcp_client.list_tools()`，直到成功後才注入 `agent_service`。
- 在 `lifespan` 主線程中改用 `asyncio.create_task(lazy_mcp_neural_wiring())` 啟動它。

## Verification Plan

### Automated Tests
- 執行 `uv run pytest tests/` 確認沒有破壞現有的核心流程。
- (可選) 執行 `make lint-be` 確認新的函數設計符合型別安全 (MyPy) 與排版規範 (Ruff)。

### Manual / Physical Verification
1. 建立實體驗證腳本 `scratch/verify_rate_limiter.py`，調用 `wait_for_capacity(tier="pro")`，物理斷言等待時間為 `~4.5s` 而非 `32.0s`。
2. 啟動 `docker compose --profile backend up` 或本地直接啟動服務，故意讓 MCP Server 掛點（或延遲啟動），觀察主伺服器是否依然能在 1 秒內啟動完畢，並在背景不斷印出 `Probing MCP Server...` 直到 MCP 上線後動態自癒。
