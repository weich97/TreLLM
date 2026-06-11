from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v03_evidence_index_maps_artifacts_and_open_gaps(tmp_path: Path):
    output_dir = tmp_path / "evidence_index"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_v03_evidence_index.py",
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Artifacts indexed: 7" in result.stdout
    assert "Open gaps: 2" in result.stdout

    summary = json.loads((output_dir / "v0_3_evidence_index.json").read_text(encoding="utf-8"))
    artifacts = list(csv.DictReader((output_dir / "v0_3_evidence_index.csv").open(encoding="utf-8")))
    coverage = list(csv.DictReader((output_dir / "v0_3_claim_coverage.csv").open(encoding="utf-8")))
    gaps = list(csv.DictReader((output_dir / "v0_3_open_gaps.csv").open(encoding="utf-8")))
    markdown = (output_dir / "v0_3_evidence_index.md").read_text(encoding="utf-8")

    assert summary["schema"] == "trellm_v0_3_evidence_index_v0.1"
    assert summary["protocol_id"] == "trellm-v0.3-iclr-protocol"
    assert summary["present_artifact_count"] == 7
    assert summary["covered_artifact_count"] == 11
    assert summary["covered_fixture_count"] == 8
    assert summary["required_protocol_artifact_count"] == 12
    assert summary["headline_scientific_claim_ready"] is False
    assert summary["open_gaps"] == [
        "direct_api_model_matrix",
        "external_reproduction_reports",
    ]
    assert "do not yet support headline scientific model-performance claims" in summary["claim_boundary"]

    assert {row["artifact_id"] for row in artifacts} == {
        "direct_api_pilot",
        "direct_api_matrix_gate",
        "execution_ladder",
        "finaudit_pilot",
        "memory_contamination",
        "power_detectable_effect_note",
        "external_reproduction_gate",
    }
    assert {row["status"] for row in artifacts} == {"present"}
    assert {row["supports_headline_claim"] for row in artifacts} == {"false"}
    assert all(row["artifact_sha256"].startswith("sha256:") for row in artifacts)
    assert any("BH-FDR" in row["statistical_methods"] for row in artifacts)
    assert any("kendall_tau" in row["statistical_methods"] for row in artifacts)
    assert any("detectable_effect_grid" in row["statistical_methods"] for row in artifacts)
    assert any("seed_sample_threshold_gate" in row["statistical_methods"] for row in artifacts)
    assert any("independent_report_count_gate" in row["statistical_methods"] for row in artifacts)

    external = next(row for row in coverage if row["required_artifact"] == "external reproduction bundle")
    assert external["coverage_status"] == "open-gap"
    assert external["evidence_ref"] == "gap:external_reproduction_reports"
    power_note = next(row for row in coverage if row["required_artifact"] == "power curve or detectable effect note")
    assert power_note["coverage_status"] == "covered-by-artifact"
    assert power_note["evidence_ref"] == "power_detectable_effect_note"
    matrix_gate = next(row for row in coverage if row["required_artifact"] == "direct API model matrix gate")
    assert matrix_gate["coverage_status"] == "covered-by-artifact"
    assert matrix_gate["evidence_ref"] == "direct_api_matrix_gate"
    reproduction_gate = next(row for row in coverage if row["required_artifact"] == "external reproduction report gate")
    assert reproduction_gate["coverage_status"] == "covered-by-artifact"
    assert reproduction_gate["evidence_ref"] == "external_reproduction_gate"
    assert sum(1 for row in coverage if row["coverage_status"] == "covered-by-fixture") == 8
    assert sum(1 for row in coverage if row["coverage_status"] == "covered-by-artifact") == 3

    assert {row["gap_id"] for row in gaps} == set(summary["open_gaps"])
    assert any(row["blocking_level"] == "headline-scientific-claim" for row in gaps)
    direct_gap = next(row for row in gaps if row["gap_id"] == "direct_api_model_matrix")
    assert "threshold gate exists" in direct_gap["current_status"]
    reproduction_gap = next(row for row in gaps if row["gap_id"] == "external_reproduction_reports")
    assert "v0.3 intake gate exists" in reproduction_gap["current_status"]
    assert "TreLLM v0.3 Evidence Index" in markdown
    assert "Headline scientific claim ready: `False`" in markdown
