-- AgencyTycoon.lean
-- Formal verification of mathematical properties for Agency Tycoon mechanics

-- Define the energy recovery logic (RESTING)
def recover_energy (energy : Int) : Int :=
  if energy + 20 > 100 then 100
  else energy + 20

-- Define the energy drain logic (WORKING)
def drain_energy (energy : Int) : Int :=
  if energy - 10 <= 0 then 0
  else energy - 10

-- Theorem 1: Energy will never exceed 100 after recovery
theorem energy_recovery_upper_bound (e : Int) : recover_energy e <= 100 := by
  dsimp [recover_energy]
  split
  · omega
  · omega

-- Theorem 2: Energy will never drop below 0 after drain (Exhaustion constraint)
theorem energy_drain_lower_bound (e : Int) : drain_energy e >= 0 := by
  dsimp [drain_energy]
  split
  · omega
  · omega

-- Theorem 3: Energy remains >= 0 after recovery (if it started >= 0)
theorem energy_recovery_lower_bound (e : Int) (h : e >= 0) : recover_energy e >= 0 := by
  dsimp [recover_energy]
  split
  · omega
  · omega

-- Theorem 4: Energy remains <= 100 after draining (if it started <= 100)
theorem energy_drain_upper_bound (e : Int) (h : e <= 100) : drain_energy e <= 100 := by
  dsimp [drain_energy]
  split
  · omega
  · omega

-- Define simplified GameState for formal verification
structure GameState where
  funds : Int
  reputation : Int
  backlog : Int
  cost : Int  -- constant maintenance cost per tick (e.g. rent/salaries)
  reward : Int -- reward per completed dev task

-- Define transition under "No Sales, No Active Tasks" condition (Income = 0)
def tick_no_income (s : GameState) : GameState :=
  { s with funds := s.funds - s.cost }

-- Theorem 5: Under no income, funds strictly decrease if cost > 0
theorem funds_strictly_decreases (s : GameState) (h_cost : s.cost > 0) :
  (tick_no_income s).funds < s.funds := by
  dsimp [tick_no_income]
  omega

-- Theorem 6: Funds will eventually drop below 0 if they start below cost
theorem funds_falls_below_zero_near_limit (s : GameState) (h_funds : s.funds < s.cost) :
  (tick_no_income s).funds < 0 := by
  dsimp [tick_no_income]
  omega

-- Define task backlog transition with Sales (s_active) and Dev (d_active)
-- If s_active = true, 1 task is produced.
-- If d_active = true and backlog > 0, 1 task is consumed.
def transition_backlog (backlog : Int) (s_active : Bool) (d_active : Bool) : Int :=
  let produced := if s_active then 1 else 0
  let consumed := if d_active && backlog > 0 then 1 else 0
  backlog + produced - consumed

-- Theorem 7: If Sales is inactive (s_active = false) and backlog is 0, backlog remains 0 regardless of Dev
theorem backlog_remains_zero_without_sales (d_active : Bool) :
  transition_backlog 0 false d_active = 0 := by
  dsimp [transition_backlog]
  simp


