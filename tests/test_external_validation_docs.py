from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_deterministic_baseline_quickstart_explains_external_evidence_tags():
    raw_text = (ROOT / "docs" / "deterministic_baseline_submission_quickstart.md").read_text(encoding="utf-8")
    text = " ".join(raw_text.split())

    assert "`external-submitted` only when the row comes from a non-maintainer" in text
    assert "`fully-auditable` only when the public manifest links enough artifacts" in text
    assert "Keep maintainer-generated refreshes separate from external evidence" in text
