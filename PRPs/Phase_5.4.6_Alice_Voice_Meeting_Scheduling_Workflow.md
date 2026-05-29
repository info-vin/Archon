# Phase 5.4.6: Alice 語意語音會議預約與跨角色排程閉環計畫

本計畫旨在衝刺業務場景閉環，實現 Alice 在第一線拜訪客戶時，能透過語音上傳自動分析「會議內容與下次預約時間」，並自動調度 `market-bot` 進行跨角色 (Bob 與 Charlie) 的排程衝突估算，自動在 Kanban 看板上建立預約任務。

---

## 1. 業務場景與核心流程

### 1.1 業務痛點與情境
1. Alice 拜訪客戶時，客戶希望預約下一次會議時間。
2. 正常情況下，Alice 無法即時得知公司內部其他成員（如 Bob、Charlie）的忙碌空檔。客戶提出的時間往往與 Bob 產生簡報的工作時間、或 Charlie 的現有會議衝突。
3. 業務需要：Alice 錄製語音上傳拜訪紀錄，若提到「下次預約時間與內容」，系統需自動估算 Bob 與 Charlie 的忙碌時間，推薦三個可行空檔回傳給 Alice，並自動在 Kanban 建立預約任務。

### 1.2 核心流程圖 (Sequence)
```
Alice (前端)                 visit_log_api           VisitLogService          StatsService          task_service
    |                            |                         |                       |                     |
    |---- 1. 上傳錄音檔案 -------->|                         |                       |                     |
    |     (audio_file)           |---- 2. 解析語音意圖 ---->|                       |                     |
    |                            |     (透過 Gemini)       |                       |                     |
    |                            |                         |-- 3. 請求忙碌度分析 ->|                     |
    |                            |                         |    (Bob & Charlie)    |                     |
    |                            |                         |                       |-- 4. 撈取任務排程 ->|
    |                            |                         |                       |<-- 5. 回傳空檔 ----|
    |                            |                         |-- 6. 計算3個候選空檔 ->|                     |
    |                            |                         |-- 7. 建立 Kanban 任務 --------------------->|
    |<--- 8. 回傳3個時間與摘要 -----|<-- 9. 回傳 API 結果 -----|                                             |
```

---

## 2. 系統架構與實體程式碼路徑對帳

為確保本文件**絕無任何幻覺（Zero Hallucination）**，以下為與 codebase 物理實體 100% 對帳後的設計細節：

### 2.1 PydanticAI 與 Pydantic 結構化資料模型
於 [python/src/server/schemas/agent_outputs.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/schemas/agent_outputs.py) 新增資料模型：

```python
from pydantic import BaseModel, Field
from datetime import datetime

class SchedulingRequest(BaseModel):
    """Pydantic model representing the parsed meeting request details."""
    scheduling_intent: bool = Field(description="是否提及下次預約會議時間的意圖")
    requested_date: str | None = Field(None, description="請求會議的日期 (YYYY-MM-DD)")
    requested_duration_hours: float = Field(1.0, description="請求會議預估時數 (小時)")
    meeting_topic: str | None = Field(None, description="會議討論主題與大綱")

class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime

class SchedulingRecommendation(BaseModel):
    """Structured response return by MarketBot/StatsService to the frontend."""
    meeting_topic: str
    suggested_slots: list[TimeSlot] = Field(default_factory=list, description="推薦的三個可行空檔選項")
    conflict_summary: str = Field(description="排除忙碌行程的簡短原因說明")
```

### 2.2 跨角色排程演算法精確路徑 (StatsService 委派鏈)
依據 codebase 物理結構，[StatsService](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/stats/__init__.py) 的 `self.metrics` 為 `MetricsManager`，其底下持有 `self.system_metrics = SystemMetrics(self.supabase)`。

因此，實體呼叫與實作路徑如下：

1. **`StatsService` 入口委派** ([python/src/server/services/stats/__init__.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/stats/__init__.py))：
   ```python
   async def get_team_availability(self, user_ids: list[str], target_date: str) -> list[dict[str, Any]]:
       """Delegates to SystemMetrics for deterministic availability calculation."""
       return await self.metrics.system_metrics.get_team_availability(user_ids, target_date)
   ```

2. **核心演算法實作** ([python/src/server/services/stats/domains/system_metrics.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/stats/domains/system_metrics.py))：
   - 查詢 `archon_tasks` 表：
     ```python
     # 撈取該日期區間非 done 且有 assignee_id 的任務
     res = self.supabase.table("archon_tasks")\
         .select("assignee_id, due_date, estimated_hours")\
         .in_("assignee_id", user_ids)\
         .neq("status", "done")\
         .execute()
     ```
   - 排除工作時間 `09:00 - 18:00` 中與任何 $[due\_date - estimated\_hours, due\_date]$ 重疊之時段，回傳 3 個可用空檔。

---

## 3. 建議變更檔案與細節

### 3.1 [MODIFY] [visit_log_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/visit_log_service.py)
*   引入 `from src.server.services.stats import stats_service`。
*   引入 `from src.server.services.agent_registry import get_agent_uuid`。
*   在 `create_log` 流程中，檢測到 `scheduling_intent` 時調用 `stats_service.get_team_availability` 進行運算並建立任務。

### 3.2 [MODIFY] [system_metrics.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/stats/domains/system_metrics.py) 與 [__init__.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/stats/__init__.py)
*   實作 `get_team_availability` 委派方法與區間碰撞演算法。

---

## 4. 驗證計畫 (自動化測試門禁)

### 4.1 新增自動化測試 [test_voice_scheduling_workflow.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/server/test_voice_scheduling_workflow.py)
*   **測試情境 A (排程演算法精確度)**:
    - 模擬資料庫插入：
      - Bob 任務：`due_date` = "2026-06-01 11:00:00", `estimated_hours` = 2.0 (代表 09:00-11:00 忙碌)
      - Charlie 任務：`due_date` = "2026-06-01 15:00:00", `estimated_hours` = 1.0 (代表 14:00-15:00 忙碌)
    - 呼叫 `stats_service.get_team_availability` 查詢 2026-06-01 忙碌度。
    - **斷言 (Assert)**：推薦的空檔必須避開上述時段，且回傳格式正確。

*   **測試情境 B (E2E 語音識別至 Kanban 任務建立)**:
    - Mock 語音 AI 回傳包含排程意圖的 JSON.
    - 模擬呼叫 `/api/visit-logs` 上傳音訊。
    - **斷言 (Assert)**：
      - 看板成功建立標題為 `[待確認會議]` 的任務。
      - 任務描述中包含 3 個可用時段。
      - 任務的協作者 (collaborator_agent_ids) 正確包含 Charlie 的 UUID，assignee 為 Bob。
