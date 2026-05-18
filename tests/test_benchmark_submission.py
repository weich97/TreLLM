from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tradearena.core.reproducibility import compute_reproducibility_hash, hash_trajectory_file
from tradearena.evaluation.submissions import validate_submission_file


ROOT = Path(__file__).resolve().parents[1]


def test_example_redacted_submission_validates_and_hash_matches():
    path = ROOT / "examples/benchmark_submissions/example_redacted_submission.json"
    payload, errors = validate_submission_file(path)

    assert errors == []
    assert payload["reproducibility_hash"] == compute_reproducibility_hash(payload)
    assert payload["redaction"]["raw_provider_text_removed"] is True


def test_cli_submission_registry_and_hash_run(tmp_path: Path):
    submission = ROOT / "examples/benchmark_submissions/example_redacted_submission.json"
    registry = tmp_path / "registry.md"
    csv_path = tmp_path / "registry.csv"
    html_path = tmp_path / "registry.html"

    subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "validate-submission", str(submission)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "tradearena.cli",
            "build-registry",
            str(submission.parent),
            "--output",
            str(registry),
            "--csv-output",
            str(csv_path),
            "--html-output",
            str(html_path),
        ],
        cwd=ROOT,
        check=True,
    )

    assert "quickstart_core_synthetic_v0_1" in registry.read_text(encoding="utf-8")
    assert "reproducibility_hash" in csv_path.read_text(encoding="utf-8")
    assert "Community Benchmark Registry" in html_path.read_text(encoding="utf-8")


def test_hash_run_produces_stable_trajectory_fingerprint():
    trajectory = ROOT / "outputs/examples/audit_walkthrough_trajectory.json"
    if not trajectory.exists():
        subprocess.run([sys.executable, "examples/audit_trajectory_walkthrough.py"], cwd=ROOT, check=True)

    direct = hash_trajectory_file(trajectory)
    result = subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "hash-run", str(trajectory)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    via_cli = json.loads(result.stdout)

    assert via_cli["file_sha256"] == direct["file_sha256"]
    assert via_cli["reproducibility_hash"] == direct["reproducibility_hash"]


def test_tradearena_public_namespace_imports_core_modules():
    import tradearena
    import tradearena.core.domain

    assert tradearena.TradeArena.__name__ == "TradeArena"
    assert tradearena.core.domain.Bar.__name__ == "Bar"
