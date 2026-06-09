-- AuditParity.lean
-- Lean 4 Spec verification for Phase 5.6.4 RBAC, Workflow and Short-circuiting Dual Judge

-- ==========================================
-- 戰線一：RBAC 動態與靜態等價定理
-- ==========================================

inductive Role
  | system_admin
  | manager
  | sales
  | marketing
  | employee
  | ai_agent

def has_permission_assign_static (role : Role) (target : Role) : Bool :=
  match role, target with
  | Role.system_admin, _ => true
  | Role.manager, Role.system_admin => false
  | Role.manager, _ => true
  | Role.sales, Role.sales => true
  | Role.sales, Role.ai_agent => true
  | Role.sales, _ => false
  | Role.marketing, Role.marketing => true
  | Role.marketing, Role.ai_agent => true
  | Role.marketing, _ => false
  | Role.employee, Role.employee => true
  | Role.employee, Role.ai_agent => true
  | Role.employee, _ => false
  | Role.ai_agent, Role.ai_agent => true
  | Role.ai_agent, _ => false

structure RBACMatrix where
  has_permission : Role → Role → Bool

def has_permission_assign_dynamic (role : Role) (target : Role) (matrix : RBACMatrix) : Bool :=
  matrix.has_permission role target

theorem assign_parity (role : Role) (target : Role) (matrix : RBACMatrix)
  (h_sync : ∀ r t, matrix.has_permission r t = has_permission_assign_static r t) :
  has_permission_assign_dynamic role target matrix = true ↔ has_permission_assign_static role target = true := by
  constructor
  · intro h
    unfold has_permission_assign_dynamic at h
    rw [← h_sync]
    exact h
  · intro h
    unfold has_permission_assign_dynamic
    rw [h_sync]
    exact h


-- ==========================================
-- 戰線二：跨角色工作流狀態機轉換安全定理
-- ==========================================

inductive WorkflowState
  | empty
  | pending_approval
  | approved
  | published

inductive WorkflowAction
  | submit_draft
  | approve
  | reject
  | finalize

def step (s : WorkflowState) (act : WorkflowAction) : WorkflowState :=
  match s, act with
  | WorkflowState.empty, WorkflowAction.submit_draft => WorkflowState.pending_approval
  | WorkflowState.pending_approval, WorkflowAction.approve => WorkflowState.approved
  | WorkflowState.pending_approval, WorkflowAction.reject => WorkflowState.empty
  | WorkflowState.approved, WorkflowAction.finalize => WorkflowState.published
  | _, _ => s

theorem workflow_safety (s1 s2 : WorkflowState) (act : WorkflowAction)
  (h_start : s1 = WorkflowState.pending_approval)
  (h_step : step s1 act = s2)
  (h_not_approve : act ≠ WorkflowAction.approve) :
  s2 ≠ WorkflowState.approved ∧ s2 ≠ WorkflowState.published := by
  rw [h_start] at h_step
  constructor
  · intro hc
    rw [← h_step] at hc
    cases act with
    | submit_draft => nomatch hc
    | approve => contradiction
    | reject => nomatch hc
    | finalize => nomatch hc
  · intro hc
    rw [← h_step] at hc
    cases act with
    | submit_draft => nomatch hc
    | approve => contradiction
    | reject => nomatch hc
    | finalize => nomatch hc


-- ==========================================
-- 戰線三：雙軌裁判短路求值正確性定理
-- ==========================================

structure UISnapshot where
  data_is_valid : Bool
  visual_is_valid : Bool

def data_check (x : UISnapshot) : Bool :=
  x.data_is_valid

def visual_check (x : UISnapshot) : Bool :=
  x.visual_is_valid

def dual_judge (x : UISnapshot) : Bool :=
  data_check x && visual_check x

theorem dual_judge_short_circuit (x : UISnapshot) (h_data : data_check x = false) :
  dual_judge x = false := by
  unfold dual_judge
  rw [h_data]
  rfl
