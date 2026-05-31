from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from tradearena.core.reproducibility import compute_reproducibility_hash, hash_trajectory_file
from tradearena.evaluation.evidence import evidence_payload
from tradearena.evaluation.submissions import (
    build_registry_rows,
    validate_submission,
    validate_submission_file,
    write_registry_html,
)

ROOT = Path(__file__).resolve().parents[1]
SUBPROCESS_ENV = {
    **os.environ,
    "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", ""),
}


def test_example_redacted_submission_validates_and_hash_matches():
    path = ROOT / "examples/benchmark_submissions/example_redacted_submission.json"
    payload, errors = validate_submission_file(path)

    assert errors == []
    assert payload["reproducibility_hash"] == compute_reproducibility_hash(payload)
    assert payload["redaction"]["raw_provider_text_removed"] is True
    assert payload["evidence"]["tags"] == ["stress-only", "deterministic-baseline"]


def test_example_llm_redacted_submission_includes_model_audit_fields():
    path = ROOT / "examples/benchmark_submissions/example_llm_redacted_submission.json"
    payload, errors = validate_submission_file(path)

    assert errors == []
    assert payload["agent"]["provider"] == "poe"
    assert payload["agent"]["prompt_mode"] == "rationale"
    assert payload["agent"]["risk_feedback_mode"] == "true"
    assert 0 <= payload["agent"]["parse_coverage"] <= 1
    assert payload["trajectory_manifest"]["artifact_hashes"]
    assert payload["evidence"]["tags"] == ["stress-only", "cached-provider", "redacted-prompt"]


def test_evidence_payload_adds_claim_and_tier_layers():
    evidence = evidence_payload(["stress-only", "cached-provider", "redacted-prompt"])

    assert evidence["claim_class"] == "benchmark"
    assert evidence["evidence_tier"] == "stress-benchmark"
    assert "Do not read this row as calibrated transaction-cost prediction." in evidence["boundary_notes"]


def test_submission_rejects_stress_only_calibrated_execution_overclaim():
    path = ROOT / "examples/benchmark_submissions/example_redacted_submission.json"
    payload, errors = validate_submission_file(path)
    assert errors == []

    overclaim = deepcopy(payload)
    overclaim["evidence"]["claim_scope"] = "broker-grade calibrated transaction-cost prediction"

    assert "stress-only evidence cannot claim calibrated or broker-grade transaction-cost validity" in validate_submission(
        overclaim,
        verify_hash=False,
    )


def test_submission_rejects_mismatched_claim_layers():
    path = ROOT / "examples/benchmark_submissions/example_redacted_submission.json"
    payload, errors = validate_submission_file(path)
    assert errors == []

    mismatched = deepcopy(payload)
    mismatched["evidence"]["claim_class"] = "scientific"
    mismatched["evidence"]["evidence_tier"] = "fill-replay-validated"

    validation_errors = validate_submission(mismatched, verify_hash=False)

    assert "evidence.claim_class must be 'benchmark' for tags stress-only;deterministic-baseline" in validation_errors
    assert "evidence.evidence_tier must be 'stress-benchmark' for tags stress-only;deterministic-baseline" in validation_errors


def test_submission_allows_quote_calibrated_boundary():
    path = ROOT / "examples/benchmark_submissions/example_redacted_submission.json"
    payload, errors = validate_submission_file(path)
    assert errors == []

    calibrated = deepcopy(payload)
    calibrated["evidence"] = evidence_payload(["quote-calibrated", "deterministic-baseline", "fully-auditable"])
    calibrated["evidence"]["claim_scope"] = "quote-calibrated execution evidence for a deterministic baseline"

    assert validate_submission(calibrated, verify_hash=False) == []


def test_submission_allows_scientific_class_only_with_strong_evidence():
    path = ROOT / "examples/benchmark_submissions/example_redacted_submission.json"
    payload, errors = validate_submission_file(path)
    assert errors == []

    scientific = deepcopy(payload)
    scientific["evidence"] = evidence_payload(["external-submitted", "fully-auditable", "fill-replay-validated"])
    scientific["evidence"]["claim_scope"] = "scientific model skill claim with independent fill replay evidence"

    assert scientific["evidence"]["claim_class"] == "scientific"
    assert validate_submission(scientific, verify_hash=False) == []


def test_cli_submission_registry_and_hash_run(tmp_path: Path):
    submission = ROOT / "examples/benchmark_submissions/example_redacted_submission.json"
    registry = tmp_path / "registry.md"
    csv_path = tmp_path / "registry.csv"
    html_path = tmp_path / "registry.html"

    subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "validate-submission", str(submission)],
        cwd=ROOT,
        env=SUBPROCESS_ENV,
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
        env=SUBPROCESS_ENV,
        check=True,
    )

    assert "quickstart_core_synthetic_v0_1" in registry.read_text(encoding="utf-8")
    assert "`stress-only`" in registry.read_text(encoding="utf-8")
    assert "stress-benchmark" in registry.read_text(encoding="utf-8")
    assert "evidence_tags" in csv_path.read_text(encoding="utf-8")
    assert "evidence_tier" in csv_path.read_text(encoding="utf-8")
    assert "Community Benchmark Registry" in html_path.read_text(encoding="utf-8")
    assert "stress-only" in html_path.read_text(encoding="utf-8")
    assert "deterministic-baseline" in html_path.read_text(encoding="utf-8")
    assert "Reproducible" in html_path.read_text(encoding="utf-8")
    assert "Redacted" in html_path.read_text(encoding="utf-8")
    assert "<details>" in html_path.read_text(encoding="utf-8")


def test_script_submission_registry_entries_work_without_installed_package(tmp_path: Path):
    submission = ROOT / "examples/benchmark_submissions/example_redacted_submission.json"
    registry = tmp_path / "script_registry.md"
    csv_path = tmp_path / "script_registry.csv"
    html_path = tmp_path / "script_registry.html"

    subprocess.run(
        [sys.executable, "scripts/validate_benchmark_submission.py", str(submission)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/build_benchmark_registry.py",
            str(submission),
            "--output",
            str(registry),
            "--csv-output",
            str(csv_path),
            "--html-output",
            str(html_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "`stress-only`" in registry.read_text(encoding="utf-8")
    assert "evidence_tags" in csv_path.read_text(encoding="utf-8")
    assert "Community Benchmark Registry" in html_path.read_text(encoding="utf-8")


def test_registry_entry_ids_and_empty_html_are_stable(tmp_path: Path):
    submission_dir = ROOT / "examples/benchmark_submissions"
    rows, errors = build_registry_rows(submission_dir)
    assert errors == []

    entry_ids = {row["reproducibility_hash"]: row["entry_id"] for row in rows}
    rows_again, errors_again = build_registry_rows(submission_dir)
    assert errors_again == []
    assert entry_ids == {row["reproducibility_hash"]: row["entry_id"] for row in rows_again}

    html_path = tmp_path / "empty_registry.html"
    write_registry_html([], html_path)
    html = html_path.read_text(encoding="utf-8")

    assert "No accepted submissions yet." in html
    assert "Community Benchmark Registry" in html


def test_hash_run_produces_stable_trajectory_fingerprint():
    trajectory = ROOT / "outputs/examples/audit_walkthrough_trajectory.json"
    if not trajectory.exists():
        subprocess.run([sys.executable, "examples/audit_trajectory_walkthrough.py"], cwd=ROOT, check=True)

    direct = hash_trajectory_file(trajectory)
    result = subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "hash-run", str(trajectory)],
        cwd=ROOT,
        env=SUBPROCESS_ENV,
        check=True,
        capture_output=True,
        text=True,
    )
    via_cli = json.loads(result.stdout)

    assert via_cli["file_sha256"] == direct["file_sha256"]
    assert via_cli["reproducibility_hash"] == direct["reproducibility_hash"]


def test_hash_run_reports_malformed_trajectory_json(tmp_path: Path):
    trajectory = tmp_path / "broken_trajectory.json"
    trajectory.write_text('{"steps": ', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "hash-run", str(trajectory)],
        cwd=ROOT,
        env=SUBPROCESS_ENV,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Trajectory file must contain valid JSON" in result.stdout
    assert "Traceback" not in result.stderr


def test_tradearena_public_namespace_imports_core_modules():
    import tradearena
    import tradearena.core.domain

    assert tradearena.TradeArena.__name__ == "TradeArena"
    assert tradearena.core.domain.Bar.__name__ == "Bar"
