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
