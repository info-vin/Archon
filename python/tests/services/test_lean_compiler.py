# python/tests/services/test_lean_compiler.py

from src.server.services.lean.compiler_service import LeanCompilerService


def test_parse_lake_errors_single():
    compiler = LeanCompilerService()
    sample_output = (
        "lean_proofs/LeanProofs/Basic.lean:4:2: error: type mismatch\n"
        "  rfl\n"
        "has type\n"
        "  n + m = n + m\n"
        "but is expected to have type\n"
        "  n + m = m + n\n"
    )
    errors = compiler.parse_lake_errors(sample_output)

    assert len(errors) == 1
    assert errors[0]["file"] == "lean_proofs/LeanProofs/Basic.lean"
    assert errors[0]["line"] == 4
    assert errors[0]["column"] == 2
    assert "type mismatch" in errors[0]["message"]
    assert "but is expected to have type" in errors[0]["message"]

def test_parse_lake_errors_multiple():
    compiler = LeanCompilerService()
    sample_output = (
        "lean_proofs/LeanProofs/Basic.lean:4:2: error: error 1\n"
        "some detail lines here\n"
        "\n"
        "lean_proofs/LeanProofs/Advanced.lean:10:5: error: error 2\n"
        "more details\n"
    )
    errors = compiler.parse_lake_errors(sample_output)

    assert len(errors) == 2
    assert errors[0]["file"] == "lean_proofs/LeanProofs/Basic.lean"
    assert errors[0]["line"] == 4
    assert "error 1" in errors[0]["message"]

    assert errors[1]["file"] == "lean_proofs/LeanProofs/Advanced.lean"
    assert errors[1]["line"] == 10
    assert "error 2" in errors[1]["message"]
