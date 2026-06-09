# Phase 5.6.5 - 形式化硬化與多租戶安全防禦規格

本文件為 Archon 系統在 Phase 5.6.5 階段針對 **RAG 語意搜尋邊界**、**Token 預算熔斷器**、與 **多租戶 RLS 物理隔離** 進行形式化安全性設計與驗證的規格說明書。

---

## 1. RAG 知識庫語意搜尋之「假陽性」限縮規格

### 1.1 痛點背景
在向量相似度檢索（Cosine Similarity）中，當使用者發問時，RAG 模組會根據向量距離提取最相似的知識切片。然而，若知識庫中無相關內容，檢索出來的最相似切片本質上是無關的（假陽性，Semantic False Positive），這會導致 AI 代理人讀取無關上下文並產生幻覺解答。

### 1.2 數學底層理論：相似度閾值邊界限縮 (Similarity Boundary Constraint)
為了防止假陽性，必須在執行期對餘弦相似度設下硬性門檻 $\theta$。
定義發問向量為 $q$，知識庫切片向量為 $d$。相似度函數為：
$$ \text{Sim}(q, d) = \frac{q \cdot d}{\|q\| \|d\|} $$
若 $\text{Sim}(q, d) < \theta$，則該切片必須被強制裁剪，且系統自動觸發「3-Tier Fallback 離線/備用模型降階」或提示「查無此知識項目」，不得將該 Chunk 送入 LLM 上下文中。

### 1.3 Lean 4 形式化驗證定理
我們將在 Lean 4 中定義相似度裁剪函數與檢索安全性：
```lean
-- 證明若相似度低於閾值，則 Chunk 必不被採納為上下文
theorem rag_semantic_safety
  (q : Vector Float n)
  (d : Chunk)
  (theta : Float)
  (h_low_sim : similarity q d < theta) :
  is_accepted_context q d theta = false
```

---

## 2. 預算熔斷器 (Budget Guard) 之單一事實累加安全規格

### 2.1 痛點背景
多 Agent 在進行非同步併發討論（如星型群聊）時，如果沒有即時統計累加費用，非同步的延遲可能導致在觸發熔斷前，多個 Bot 已經發起大量高成本的 API 呼叫，造成 Token 預算被「偷渡超支（Race-Condition Cost Overrun）」。

### 2.2 數學底層理論：單調遞增序列與上界阻斷 (Monotonic cost upper-bound)
在狀態機的每次轉移中，累積的 Token 開銷 $C_t$ 必須是**單調遞增**的：
$$ \forall t, \quad C_{t+1} \ge C_t $$
一旦 $C_t > B$（$B$ 為總預算上限），系統必須立即物理封鎖所有非 GET 請求（回傳 HTTP 402），且此「封鎖狀態（Blocked State）」在狀態機的未來轉移中具有強大且不可逆的單向性（一旦 Blocked，後續所有狀態皆必為 Blocked）。

### 2.3 Lean 4 形式化驗證定理
在狀態機模型中證明：
```lean
-- 證明若某一步已超額，後續任何操作皆會被鎖死在 Blocked 狀態
theorem budget_guard_monotonic_blocking
  (s : SystemState)
  (t : Nat)
  (h_exceeded : s.accumulated_cost > s.budget_limit) :
  (future_state s t).is_api_blocked = true
```

---

## 3. 多租戶 RLS 物理隔離之「零洩漏」安全性規格

### 3.1 痛點背景
在 SaaS 架構中，雖然實作了 Supabase Row Level Security (RLS) 政策，但若開發者在編寫自訂 SQL 函數或中介軟體時忘記處理 Session JWT 中的 `tenant_id`，或者 RLS 政策存在循環依賴（Recursive Policy），可能導致資料庫將租戶 A 的敏感 Leads 或是專案資料洩漏給租戶 B。

### 3.2 數學底層理論：關係代數投影嚴格分區 (Relational Partitioning Invariant)
在關係資料庫中，資料表 $R$ 根據 `tenant_id` 進行物理或邏輯分區。
對於任意租戶 $A$ 與 $B$ 的 Session JWT 標記 $T_A$ 與 $T_B$，若 $T_A \neq T_B$，則他們透過 RLS 政策篩選出的子集 $R_A$ 與 $R_B$ 之交集，必須在數學上恆等於空集：
$$ R_A \cap R_B = \emptyset $$

### 3.3 Lean 4 形式化驗證定理
我們將在 Lean 4 中建立關係查詢篩選模型，並證明無洩漏定理：
```lean
-- 證明不同租戶身分下查詢結果交集恆為空
theorem rls_zero_leakage_guarantee
  (tenant_a tenant_b : TenantId)
  (h_neq : tenant_a ≠ tenant_b)
  (query_a : QueryResult tenant_a)
  (query_b : QueryResult tenant_b) :
  Disjoint query_a.rows query_b.rows
```

---

## 4. 自動化品質門禁與測試對帳

於 Phase 5.6.5 實作時，我們將遵循以下自動化檢驗標準：
1.  **Lake 定理編譯**：所有上述定理（`rag_semantic_safety`、`budget_guard_monotonic_blocking`、`rls_zero_leakage_guarantee`）必須註冊在 `lean_proofs/` 中，並通過 `make test-lean`。
2.  **Pytest 雙向物理對帳**：
    *   在 `test_lean_model_alignment.py` 中，自動核對實際資料庫 `leads` 與 `projects` 的 RLS 啟用狀態，與 Lean 中的 `Relational Partitioning` 假設對齊。
    *   自動核對 `BudgetGuardMiddleware` 中宣告的預算變數，與 Lean 中 $B$ 限制參數對齊。
3.  **終極網關通過**：通過 `make audit-qa` 的全套自動化 E2E 與單元測試，無任何代碼與規格之退化。
