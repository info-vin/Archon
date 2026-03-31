from src.server.services.stats_service import StatsService


def test_calculate_ai_score_grounded_logic():
    stats = StatsService()

    # 1. Test basic quality (Word count based)
    assert stats.calculate_ai_score("Very short content") == 50  # < 50 words penalty

    long_content = "Word " * 201  # 200+ words to pass all length checks
    assert stats.calculate_ai_score(long_content) == 100

    # 2. Test Technical Metadata (Phase 4.6.15 Physical indicators)
    meta_fail = {"returncode": 1, "lint_passed": False}
    # Length passes (100) - technical penalty (40 + 15) = 45
    score_fail = stats.calculate_ai_score("Word " * 201, meta_fail)
    assert score_fail == 45

    meta_pass = {"returncode": 0, "lint_passed": True}
    score_pass = stats.calculate_ai_score("Word " * 201, meta_pass)
    assert score_pass == 100

    # 3. Test required terms
    meta_terms = {"required_terms": ["Archon"]}
    # Length passes (100) - Missing keyword (10) = 90
    assert stats.calculate_ai_score("Word " * 201, meta_terms) == 90
    # Length passes (100) + Keyword (0 penalty) = 100
    assert stats.calculate_ai_score("Word " * 201 + " Archon", meta_terms) == 100

    # 4. Test Safety
    assert stats.calculate_ai_score("This contains CONFIDENTIAL information." + " Word" * 200) == 50
