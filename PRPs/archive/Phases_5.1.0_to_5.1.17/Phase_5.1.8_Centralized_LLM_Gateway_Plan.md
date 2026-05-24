# Phase 5.1.8 實作計畫 (Implementation Plan) - Centralized LLM Gateway

**適用對象**: 系統分析師 (SA)、後端開發者
**目的**: 建立全系統唯一的 LLM 流量出口，解決多容器併發衝破 Free Tier 限制之問題。
**最後更新**: 2026-05-19
**狀態**: 🟢 已物理落地 (Physical Realized)

---

## 1. 背景與動機 (Background)
Archon 系統拆分為 5 個微服務後，`archon-agents` 與 `archon-mcp` 直接持金鑰呼叫外部 API。這導致 `archon-server` 的 RateLimiter 產生盲區，多容器併發請求引發頻繁的 429 Resource Exhausted 錯誤，並在 5173 David 看板產生大量例外日誌。

## 2. 解決方案 (Proposed Solution - Option A)
將 `archon-server` (Port 8181) 升格為 **Internal LLM Gateway**。

### 2.1 核心架構
- **Gateway Endpoint**: 在 `archon-server` 新增 `/internal/llm/gemini/v1beta/` 代理路由。
- **Rate Limiting**: 代理路由強制繼承 `ThreadingService` 的單線化排隊機制 (`max_concurrent=1`)。
- **Secret Management**: 金鑰統一由 `archon-server` 託管，其餘容器僅需指向 Gateway URL。

## 3. 實作細節 (Physical Implementation)

### 3.1 後端代理路由 (archon-server)
- **檔案**: `python/src/server/api_routes/internal_llm_api.py`
- **邏輯**: 使用 `httpx.AsyncClient` 轉發請求至 Google API，並自動注入 `GEMINI_API_KEY`。

### 3.2 Agent 彈性驅動 (archon-agents)
- **檔案**: `python/src/agents/utils/resilience.py`
- **邏輯**: 偵測 `API_GATEWAY_URL` 環境變數，透過 PydanticAI 的 `GoogleProvider(base_url=...)` 重新導向流量。

### 3.3 容器編排 (Docker)
- **檔案**: `docker-compose.yml`
- **變動**: 移除 `archon-mcp` 與 `archon-agents` 的 API Keys，改為注入 `API_GATEWAY_URL`。

## 4. 驗收標準 (Quality Gates)
- [x] **物理貫通**: 執行 `make twin-scout` 確保所有角色工作流不因 Gateway 轉發產生 404。
- [x] **監控連動**: 5173 David 看板的 Token Usage Table 必須能捕捉到來自 Agents 的代理請求。
- [x] **資源匹配**: 在高併發測試下，系統應表現為「優雅排隊」而非「429 崩潰」。

---

## 5. 核心工程教訓 (Lessons Learned)
1. **分散式盲目競爭是 Free Tier 的天敵**: 在資源極度受限的環境下，物理隔離的微服務必須共享同一個「算力網關 (Compute Gateway)」，否則 RateLimiter 將失去意義。
2. ** trailing slash 的細節**: PydanticAI 的 Provider 在拼接路徑時，`base_url` 末尾的斜線影響甚大，必須確保 Docker 配置與代碼解析一致。
