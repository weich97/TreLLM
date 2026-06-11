from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ID = "trellm-v0.3-iclr-protocol"
DEFAULT_OUTPUT_DIR = "docs/results/v0_3_evidence_index"

ARTIFACT_SPECS = [
    {
        "artifact_id": "direct_api_pilot",
        "claim_area": "direct API provenance",
        "summary_path": "docs/results/v0_3_direct_api_pilot/direct_api_pilot_summary.json",
        "primary_rows": "docs/results/v0_3_direct_api_pilot/direct_api_pilot_rows.csv",
        "claim_class": "engineering",
        "evidence_stage": "protocol-fixture",
        "supports_headline_claim": False,
        "statistical_methods": ["seed/sample manifest coverage"],
        "claim_boundary": "Validates direct API evidence plumbing without live provider calls.",
    },
    {
        "artifact_id": "direct_api_matrix_gate",
        "claim_area": "direct API model matrix threshold gate",
        "summary_path": "docs/results/v0_3_direct_api_matrix_gate/direct_api_matrix_gate_summary.json",
        "primary_rows": "docs/results/v0_3_direct_api_matrix_gate/direct_api_matrix_gate_coverage.csv",
        "claim_class": "engineering",
        "evidence_stage": "threshold-gate",
        "supports_headline_claim": False,
        "statistical_methods": ["direct_manifest_hash_binding", "seed_sample_threshold_gate"],
        "claim_boundary": "Verifies direct API matrix provenance and 10x3 coverage; current fixture rows remain pilot evidence.",
    },
    {
        "artifact_id": "direct_api_model_matrix_plan",
        "claim_area": "direct API model matrix run plan and credential preflight",
        "summary_path": "docs/results/v0_3_direct_api_matrix_plan/direct_api_matrix_plan_summary.json",
        "primary_rows": "docs/results/v0_3_direct_api_matrix_plan/direct_api_matrix_plan_coverage.csv",
        "claim_class": "engineering",
        "evidence_stage": "planning-note",
        "supports_headline_claim": False,
        "statistical_methods": ["pre_registered_10x3_matrix_plan", "credential_env_var_preflight"],
        "claim_boundary": "Pre-registers direct API matrix rows and credential readiness; not provider-performance evidence.",
    },
    {
        "artifact_id": "direct_api_submission_checklist",
        "claim_area": "direct API redaction and submission checklist",
        "summary_path": "docs/results/v0_3_direct_api_submission_checklist/direct_api_submission_checklist_summary.json",
        "primary_rows": "docs/results/v0_3_direct_api_submission_checklist/direct_api_submission_checklist_items.csv",
        "claim_class": "engineering",
        "evidence_stage": "planning-note",
        "supports_headline_claim": False,
        "statistical_methods": ["schema_field_coverage_check", "redaction_submission_checklist"],
        "claim_boundary": "Constrains direct API redaction, manifest binding, and claim boundaries; not provider-performance evidence.",
    },
    {
        "artifact_id": "execution_ladder",
        "claim_area": "execution assumption sensitivity",
        "summary_path": "docs/results/v0_3_execution_ladder/execution_ladder_summary.json",
        "primary_rows": "docs/results/v0_3_execution_ladder/execution_ladder_rows.csv",
        "claim_class": "benchmark",
        "evidence_stage": "protocol-fixture",
        "supports_headline_claim": False,
        "statistical_methods": ["kendall_tau", "top_k_jaccard", "bootstrap_ci"],
        "claim_boundary": "Reports deterministic E0-E3 fixture sensitivity, not live-provider model skill.",
    },
    {
        "artifact_id": "finaudit_pilot",
        "claim_area": "financial trace audit",
        "summary_path": "docs/results/v0_3_finaudit_pilot/finaudit_pilot_summary.json",
        "primary_rows": "docs/results/v0_3_finaudit_pilot/finaudit_pilot_scores.csv",
        "claim_class": "engineering",
        "evidence_stage": "protocol-fixture",
        "supports_headline_claim": False,
        "statistical_methods": ["precision", "recall", "f1", "wilson_interval", "difficulty_breakdown"],
        "claim_boundary": "Validates injected-defect scoring path with fixture auditors, not model audit performance.",
    },
    {
        "artifact_id": "memory_contamination",
        "claim_area": "memory contamination mechanism",
        "summary_path": "docs/results/v0_3_memory_contamination/memory_contamination_summary.json",
        "primary_rows": "docs/results/v0_3_memory_contamination/memory_contamination_dose_response.csv",
        "claim_class": "benchmark",
        "evidence_stage": "protocol-fixture",
        "supports_headline_claim": False,
        "statistical_methods": ["paired_bootstrap_delta", "BH-FDR q_value", "bootstrap_ci"],
        "claim_boundary": "Reports C0 read-time memory pollution fixture effects, not LLM model-level robustness.",
    },
    {
        "artifact_id": "power_detectable_effect_note",
        "claim_area": "statistical power and detectable effects",
        "summary_path": "docs/results/v0_3_power_note/v0_3_power_note_summary.json",
        "primary_rows": "docs/results/v0_3_power_note/v0_3_detectable_effects.csv",
        "claim_class": "benchmark",
        "evidence_stage": "planning-note",
        "supports_headline_claim": False,
        "statistical_methods": ["paired_sign_flip_permutation_power", "detectable_effect_grid"],
        "claim_boundary": "Constrains sample-size and detectable-effect claims; not model-superiority evidence.",
    },
    {
        "artifact_id": "external_reproduction_gate",
        "claim_area": "external reproduction intake and environment coverage",
        "summary_path": "docs/results/v0_3_external_reproduction_reports/external_reproduction_gate_summary.json",
        "primary_rows": "docs/results/v0_3_external_reproduction_reports/external_reproduction_environment_coverage.csv",
        "claim_class": "engineering",
        "evidence_stage": "threshold-gate",
        "supports_headline_claim": False,
        "statistical_methods": ["environment_coverage_gate", "independent_report_count_gate"],
        "claim_boundary": "Validates external report eligibility; current accepted report count remains below the v0.3 threshold.",
    },
]

GAP_SPECS = [
    {
        "gap_id": "direct_api_model_matrix",
        "required_for": "scientific model reliability claims",
        "missing_evidence": "direct API model rows with at least 10 seeds and 3 samples per seed, or explicit pilot labeling",
        "current_status": (
            "plan/preflight and threshold gate exist; current public rows are fixture/pilot evidence and "
            "no non-fixture direct API group has run"
        ),
        "blocking_level": "headline-scientific-claim",
    },
    {
        "gap_id": "external_reproduction_reports",
        "required_for": "external reproducibility claim",
        "missing_evidence": "three independent reproduction reports covering Windows/macOS, Linux, and Colab/Binder",
        "current_status": "v0.3 intake gate exists; no accepted independent reports are present",
        "blocking_level": "external-validation-claim",
    },
]

REQUIRED_PROTOCOL_ARTIFACTS = {
    "direct-provider manifest schema or contract": "direct_api_pilot",
    "raw seed rows": "direct_api_pilot;execution_ladder;memory_contamination",
    "aggregate rows": "execution_ladder;memory_contamination",
    "significance table": "memory_contamination",
    "ranking-stability table": "execution_ladder",
    "contamination probe report": "memory_contamination",
    "execution-sensitivity report": "execution_ladder",
    "FinAudit pilot report": "finaudit_pilot",
    "power curve or detectable effect note": "power_detectable_effect_note",
    "direct API redaction and submission checklist": "direct_api_submission_checklist",
    "direct API model matrix plan": "direct_api_model_matrix_plan",
    "direct API model matrix gate": "direct_api_matrix_gate",
    "external reproduction report gate": "external_reproduction_gate",
    "external reproduction bundle": "gap:external_reproduction_reports",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a v0.3 ICLR evidence index from generated artifacts.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_rows = [_artifact_row(spec) for spec in ARTIFACT_SPECS]
    coverage_rows = _coverage_rows(artifact_rows)
    gap_rows = _gap_rows()
    summary = _summary(artifact_rows, coverage_rows, gap_rows)

    _write_csv(output_dir / "v0_3_evidence_index.csv", artifact_rows, list(artifact_rows[0]))
    _write_csv(output_dir / "v0_3_claim_coverage.csv", coverage_rows, list(coverage_rows[0]))
    _write_csv(output_dir / "v0_3_open_gaps.csv", gap_rows, list(gap_rows[0]))
    _write_json(output_dir / "v0_3_evidence_index.json", summary)
    (output_dir / "v0_3_evidence_index.md").write_text(
        _summary_markdown(summary, artifact_rows, coverage_rows, gap_rows),
        encoding="utf-8",
    )
    print(f"Wrote {_display(output_dir / 'v0_3_evidence_index.csv')}")
    print(f"Wrote {_display(output_dir / 'v0_3_claim_coverage.csv')}")
    print(f"Wrote {_display(output_dir / 'v0_3_open_gaps.csv')}")
    print(f"Wrote {_display(output_dir / 'v0_3_evidence_index.json')}")
    print(f"Wrote {_display(output_dir / 'v0_3_evidence_index.md')}")
    print(f"Artifacts indexed: {len(artifact_rows)}")
    print(f"Open gaps: {len(gap_rows)}")
    return 0


def _artifact_row(spec: dict[str, Any]) -> dict[str, Any]:
    summary_path = _resolve(spec["summary_path"])
    rows_path = _resolve(spec["primary_rows"])
    summary = _load_json(summary_path)
    missing = [path for path in (summary_path, rows_path) if not path.exists()]
    row_count = summary.get("row_count", summary.get("task_count", summary.get("score_row_count", "")))
    return {
        "protocol_id": PROTOCOL_ID,
        "artifact_id": spec["artifact_id"],
        "claim_area": spec["claim_area"],
        "claim_class": spec["claim_class"],
        "evidence_stage": spec["evidence_stage"],
        "supports_headline_claim": str(bool(spec["supports_headline_claim"])).lower(),
        "summary_path": _display(summary_path),
        "primary_rows": _display(rows_path),
        "summary_schema": summary.get("schema", ""),
        "row_count": row_count,
        "statistical_methods": ";".join(spec["statistical_methods"]),
        "claim_boundary": spec["claim_boundary"],
        "artifact_sha256": _sha256_path(summary_path) if summary_path.exists() else "",
        "primary_rows_sha256": _sha256_path(rows_path) if rows_path.exists() else "",
        "status": "missing" if missing else "present",
        "missing_paths": ";".join(_display(path) for path in missing),
    }


def _coverage_rows(artifact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_artifact = {row["artifact_id"]: row for row in artifact_rows}
    rows: list[dict[str, Any]] = []
    for required_artifact, evidence_ref in REQUIRED_PROTOCOL_ARTIFACTS.items():
        if evidence_ref.startswith("gap:"):
            rows.append(
                {
                    "protocol_id": PROTOCOL_ID,
                    "required_artifact": required_artifact,
                    "coverage_status": "open-gap",
                    "evidence_ref": evidence_ref,
                    "claim_boundary": "Required by protocol but not yet satisfied by public v0.3 artifacts.",
                }
            )
            continue
        refs = evidence_ref.split(";")
        present = [ref for ref in refs if by_artifact.get(ref, {}).get("status") == "present"]
        status = "missing"
        if present:
            stages = {str(by_artifact[ref].get("evidence_stage", "")) for ref in present}
            status = "covered-by-fixture" if "protocol-fixture" in stages else "covered-by-artifact"
        rows.append(
            {
                "protocol_id": PROTOCOL_ID,
                "required_artifact": required_artifact,
                "coverage_status": status,
                "evidence_ref": ";".join(present),
                "claim_boundary": (
                    "Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require "
                    "non-fixture direct API rows and scale thresholds."
                ),
            }
        )
    return rows


def _gap_rows() -> list[dict[str, Any]]:
    return [{"protocol_id": PROTOCOL_ID, **gap} for gap in GAP_SPECS]


def _summary(
    artifact_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    present = [row for row in artifact_rows if row["status"] == "present"]
    open_coverage = [row for row in coverage_rows if row["coverage_status"] == "open-gap"]
    return {
        "schema": "trellm_v0_3_evidence_index_v0.1",
        "protocol_id": PROTOCOL_ID,
        "artifact_count": len(artifact_rows),
        "present_artifact_count": len(present),
        "required_protocol_artifact_count": len(coverage_rows),
        "covered_artifact_count": sum(
            1 for row in coverage_rows if row["coverage_status"] in {"covered-by-fixture", "covered-by-artifact"}
        ),
        "covered_fixture_count": sum(1 for row in coverage_rows if row["coverage_status"] == "covered-by-fixture"),
        "open_gap_count": len(gap_rows),
        "open_protocol_coverage_count": len(open_coverage),
        "headline_scientific_claim_ready": False,
        "claim_boundary": (
            "This index maps public v0.3 artifacts to protocol claims. Current artifacts validate protocol "
            "plumbing and pilot mechanisms; they do not yet support headline scientific model-performance claims."
        ),
        "artifacts": [row["artifact_id"] for row in artifact_rows],
        "open_gaps": [row["gap_id"] for row in gap_rows],
    }


def _summary_markdown(
    summary: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# TreLLM v0.3 Evidence Index",
        "",
        "This index maps generated public artifacts to the v0.3 ICLR protocol claims.",
        "It is deliberately conservative: fixture and pilot artifacts do not support headline scientific model-performance claims.",
        "",
        f"- Protocol: `{summary['protocol_id']}`",
        f"- Present artifacts: `{summary['present_artifact_count']} / {summary['artifact_count']}`",
        f"- Public-artifact-covered protocol artifacts: `{summary['covered_artifact_count']} / {summary['required_protocol_artifact_count']}`",
        f"- Fixture-covered protocol artifacts: `{summary['covered_fixture_count']} / {summary['required_protocol_artifact_count']}`",
        f"- Open gaps: `{summary['open_gap_count']}`",
        f"- Headline scientific claim ready: `{summary['headline_scientific_claim_ready']}`",
        f"- Claim boundary: {summary['claim_boundary']}",
        "",
        "## Artifact Map",
        "",
        "| Artifact | Claim area | Stage | Methods | Supports headline claim | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in artifact_rows:
        lines.append(
            f"| {row['artifact_id']} | {row['claim_area']} | {row['evidence_stage']} | "
            f"{row['statistical_methods']} | {row['supports_headline_claim']} | {row['status']} |"
        )
    lines += [
        "",
        "## Protocol Coverage",
        "",
        "| Required artifact | Status | Evidence | Boundary |",
        "| --- | --- | --- | --- |",
    ]
    for row in coverage_rows:
        lines.append(
            f"| {row['required_artifact']} | {row['coverage_status']} | {row['evidence_ref']} | {row['claim_boundary']} |"
        )
    lines += [
        "",
        "## Open Gaps",
        "",
        "| Gap | Required for | Missing evidence | Current status |",
        "| --- | --- | --- | --- |",
    ]
    for row in gap_rows:
        lines.append(
            f"| {row['gap_id']} | {row['required_for']} | {row['missing_evidence']} | {row['current_status']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_path(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _display(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
