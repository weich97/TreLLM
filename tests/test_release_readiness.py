from pathlib import Path

from scripts.check_release_readiness import _check_ci_gate_parity


def test_release_readiness_flags_missing_ci_gate(tmp_path: Path):
    ci_path = tmp_path / "ci.yml"
    ci_path.write_text(
        "\n".join(
            [
                "name: CI",
                "steps:",
                '  - run: python -m ruff check src scripts examples tests',
                "  - run: python -m pytest tests -q --cov=tradearena --cov-report=xml --cov-report=term-missing",
                "  - run: python scripts/validate_demo_artifacts.py",
                "  - run: python scripts/check_release_readiness.py",
            ]
        ),
        encoding="utf-8",
    )

    failures = _check_ci_gate_parity(ci_path)

    assert "CI workflow is missing required gate command: python -m mypy" in failures
