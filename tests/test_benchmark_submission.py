from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from tradearena.core.reproducibility import compute_reproducibility_hash, hash_trajectory_file
from tradearena.evaluation.evidence import evidence_payload
from tradearena.evaluation.submissions import validate_submission, validate_submission_file

ROOT = Path(__file__).resolve().parents[1]


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
    assert "`stress-only`" in registry.read_text(encoding="utf-8")
    assert "stress-benchmark" in registry.read_text(encoding="utf-8")
    assert "evidence_tags" in csv_path.read_text(encoding="utf-8")
    assert "evidence_tier" in csv_path.read_text(encoding="utf-8")
    assert "Community Benchmark Registry" in html_path.read_text(encoding="utf-8")
    assert "stress-only" in html_path.read_text(encoding="utf-8")
    assert "deterministic-baseline" in html_path.read_text(encoding="utf-8")


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
