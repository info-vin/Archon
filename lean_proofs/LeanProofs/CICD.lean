-- CICD.lean
inductive State
  | pending
  | running
  | success
  | rollback

def transition (s : State) (event : String) : State :=
  match s, event with
  | State.pending, "run_tests" => State.running
  | State.running, "tests_pass" => State.success
  | State.running, "tests_fail" => State.rollback
  | _, _ => s

theorem safety_gate (s : State) (h : s = State.pending) :
  transition s "deploy" ≠ State.success := by
  rw [h]
  intro hc
  nomatch hc
