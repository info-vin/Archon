-- CardBattler.lean
-- Formal verification of mathematical properties and invariants for the Card Battler.

-- Define the normalization clamp function for natural numbers
def clamp (val : Nat) (min_val : Nat) (max_val : Nat) : Nat :=
  if val < min_val then min_val
  else if val > max_val then max_val
  else val

-- Normalization definitions
def calculate_cost (files_changed : Nat) : Nat :=
  clamp files_changed 1 3

def calculate_damage (insertions : Nat) : Nat :=
  clamp (insertions / 10) 5 50

def calculate_block (deletions : Nat) : Nat :=
  clamp (deletions / 5) 0 30

-- Theorem 1: Cost is always bounded between 1 and 3
theorem cost_lower_bound (f : Nat) : calculate_cost f >= 1 := by
  dsimp [calculate_cost, clamp]
  split
  · omega
  · split
    · omega
    · omega

theorem cost_upper_bound (f : Nat) : calculate_cost f <= 3 := by
  dsimp [calculate_cost, clamp]
  split
  · omega
  · split
    · omega
    · omega

-- Theorem 2: Damage is always bounded between 5 and 50
theorem damage_lower_bound (i : Nat) : calculate_damage i >= 5 := by
  dsimp [calculate_damage, clamp]
  split
  · omega
  · split
    · omega
    · omega

theorem damage_upper_bound (i : Nat) : calculate_damage i <= 50 := by
  dsimp [calculate_damage, clamp]
  split
  · omega
  · split
    · omega
    · omega

-- Theorem 3: Block is always bounded between 0 and 30
theorem block_lower_bound (d : Nat) : calculate_block d >= 0 := by
  dsimp [calculate_block, clamp]
  split
  · omega
  · omega

theorem block_upper_bound (d : Nat) : calculate_block d <= 30 := by
  dsimp [calculate_block, clamp]
  split
  · omega
  · omega

-- Theorem 4: Playing any card (cost >= 1) strictly decreases mana
theorem mana_decrease (mana cost : Nat) (h_cost : cost >= 1) (h_afford : mana >= cost) :
  mana - cost < mana := by
  omega
