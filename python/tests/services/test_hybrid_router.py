# python/tests/services/test_hybrid_router.py

from unittest.mock import patch

from src.server.services.llm.hybrid_router import HybridRouter


def test_evaluate_complexity_simple():
    router = HybridRouter()
    simple_proof = "theorem id_prop (P : Prop) : P -> P := by intro h; exact h"
    score = router.evaluate_complexity(simple_proof)
    # 12 words * 2 = 24. theorem (10), intro (10), exact (10). Total = 54.
    assert score > 0
    assert score < 150

def test_evaluate_complexity_complex():
    router = HybridRouter()
    complex_proof = (
        "theorem add_commute (n m : Nat) : n + m = m + n := by\n"
        "  induction n with\n"
        "  | zero => simp\n"
        "  | succ n' ih =>\n"
        "    simp\n"
        "    rw [Nat.add_succ]\n"
        "    rw [ih]\n"
        "    rw [Nat.succ_add]\n"
        "    simp\n"
        "    induction m with\n"
        "    | zero => rfl\n"
        "    | succ m' ih2 => simp [ih2]\n"
    )
    score = router.evaluate_complexity(complex_proof)
    # Lots of keywords, should score high
    assert score > 150


def test_should_escalate_rules():
    router = HybridRouter()
    router._cache.clear()

    # 1. Slow hardware trigger
    with patch("src.server.services.settings_service.SettingsService.get_setting", return_value="500"):
        assert router.should_escalate_to_cloud("simp", retry_count=0) is True

    # 2. Fast hardware
    router._cache.clear()
    with patch("src.server.services.settings_service.SettingsService.get_setting", return_value="100"):
        # Retry count trigger (K >= 2)
        assert router.should_escalate_to_cloud("simp", retry_count=2) is True
        assert router.should_escalate_to_cloud("simp", retry_count=1) is False

        # Complexity trigger (S >= 150)
        complex_proof = "theorem " * 20
        assert router.should_escalate_to_cloud(complex_proof, retry_count=0) is True
