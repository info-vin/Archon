-- Consistency.lean
def HelloConsistency := "consistency verified"

-- Define a basic node structure
structure KnowledgeNode where
  id : Nat
  is_deprecated : Bool

-- Define validity of a knowledge subset
def nodes_are_valid (nodes : List KnowledgeNode) : Prop :=
  ∀ n ∈ nodes, n.is_deprecated = false

-- Theorem: If a subset passes the validity check, all elements in it are non-deprecated
theorem subset_consistency (nodes : List KnowledgeNode) (h : nodes_are_valid nodes) :
  ∀ n ∈ nodes, n.is_deprecated = false := by
  intro n hn
  exact h n hn
