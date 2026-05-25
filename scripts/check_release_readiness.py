from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_FILE_BYTES = 25 * 1024 * 1024
REQUIRED_FILES = [
    "README.md",
    "CITATION.cff",
    "docs/getting_started.md",
    "docs/advanced_integrations_security.md",
    "docs/agent_skills.md",
    "docs/agent_skills_index.md",
    "docs/financial_audit_agent_benchmark.md",
    "docs/technical_report.md",
    "docs/benchmark_maturity.md",
    "docs/v0_2_credibility_audit.md",
    "docs/academic_report_plan.md",
    "docs/external_validation.md",
    "docs/claim_boundaries.md",
    "docs/evidence_labels.md",
    "docs/benchmark_v0_2_spec.md",
    "docs/execution_calibration_priority.md",
    "docs/execution_model_boundaries.md",
    "docs/reproduction_pack_v0_2.md",
    "docs/community_participation.md",
    "docs/community_tasks.md",
    "docs/community_operations.md",
    "docs/narrative_positioning.md",
    "docs/plugin_development.md",
    "docs/benchmark_challenges.md",
    "docs/evaluation_rigor.md",
    "docs/market_rules.md",
    "docs/observability.md",
    "docs/artifact_portability.md",
    "docs/demo_matrix.md",
    "docs/launch/release_notes_v0.2.0.md",
    "docs/launch/release_artifacts_v0.2.0.md",
    "docs/launch/release_artifacts_v0.2.0.json",
    "docs/results/benchmark_v0_2.md",
    "docs/results/llm_live_baseline.md",
    "docs/results/llm_live_baseline.json",
    "docs/results/execution_quote_fill_calibration_sample.md",
    "docs/results/execution_quote_fill_calibration_sample.json",
    "docs/results/execution_quote_fill_calibration_binance_sample.md",
    "docs/results/execution_quote_fill_calibration_binance_sample.json",
    "docs/results/llm_live_baseline_manifest/manifest.json",
    "docs/results/llm_live_baseline_manifest/poe_gpt55_live_smoke_2026-05-18_summary.json",
    "docs/results/community_registry.md",
    "docs/results/community_registry.html",
    "docs/results/model_matrix/leaderboard_model_matrix.md",
    "docs/results/model_matrix/leaderboard_model_matrix.csv",
    "docs/results/model_matrix/leaderboard_model_matrix_aggregate.csv",
    "docs/results/model_matrix/leaderboard_model_matrix_scenario_aggregate.csv",
    "docs/results/model_matrix/leaderboard_model_matrix_significance.csv",
    "docs/results/model_matrix/leaderboard_execution_shock_aggregate.csv",
    "docs/results/real_market_matrix/real_market_model_matrix.md",
    "docs/results/real_market_matrix/real_market_model_matrix.csv",
    "docs/results/real_market_matrix/real_market_model_matrix_aggregate.csv",
    "docs/results/real_market_matrix/real_market_model_matrix_scenario_aggregate.csv",
    "docs/results/real_market_matrix/real_market_model_matrix_significance.csv",
    "docs/results/real_market_matrix/real_market_walk_forward.csv",
    "docs/results/classical_baselines/classical_baselines.md",
    "docs/results/classical_baselines/classical_baseline_matrix.csv",
    "docs/results/classical_baselines/classical_baseline_aggregate.csv",
    "docs/results/classical_baselines/classical_vs_llm_comparison.csv",
    "docs/results/quality_decomposition/quality_decomposition.md",
    "docs/results/quality_decomposition/quality_decomposition_rows.csv",
    "docs/results/quality_decomposition/quality_decomposition_aggregate.csv",
    "docs/results/quality_decomposition/decision_execution_radar.svg",
    "docs/results/skill_task_matrix.md",
    "docs/demo_artifacts.yaml",
    "schemas/benchmark_submission.schema.json",
    "schemas/calibration_profile.schema.json",
    "schemas/demo_artifact_contract.schema.json",
    "schemas/reproduction_report.schema.json",
    "schemas/skill_answer_set.schema.json",
    "schemas/skill_task_rubric.schema.json",
    "schemas/trajectory.schema.json",
    "benchmarks/v0.2/spec.json",
    "examples/benchmark_submissions/example_redacted_submission.json",
    "examples/benchmark_submissions/model_matrix/calm_trend__poe_gpt_5_5.json",
    "examples/benchmark_submissions/model_matrix/liquidity_collapse__poe_gpt_5_5.json",
    "examples/benchmark_submissions/real_market_matrix/recent_cross_asset__poe_gpt_5_5__seed_7.json",
    "examples/skill_tasks/README.md",
    "examples/skill_tasks/trajectory_audit_001/input.md",
    "examples/skill_tasks/trajectory_audit_001/rubric.json",
    "examples/skill_tasks/intent_execution_autopsy_001/input.md",
    "examples/skill_tasks/intent_execution_autopsy_001/trajectory_excerpt.json",
    "examples/skill_tasks/intent_execution_autopsy_001/rubric.json",
    "examples/skill_tasks/risk_gate_review_001/input.md",
    "examples/skill_tasks/risk_gate_review_001/rubric.json",
    "examples/skill_tasks/risk_feedback_learning_001/input.md",
    "examples/skill_tasks/risk_feedback_learning_001/risk_feedback_steps.json",
    "examples/skill_tasks/risk_feedback_learning_001/rubric.json",
    "examples/skill_tasks/execution_boundary_001/input.md",
    "examples/skill_tasks/execution_boundary_001/rubric.json",
    "examples/skill_tasks/execution_attribution_001/input.md",
    "examples/skill_tasks/execution_attribution_001/execution_report.json",
    "examples/skill_tasks/execution_attribution_001/rubric.json",
    "examples/skill_tasks/claim_boundary_001/input.md",
    "examples/skill_tasks/claim_boundary_001/rubric.json",
    "examples/skill_tasks/claim_boundary_provider_drift_001/input.md",
    "examples/skill_tasks/claim_boundary_provider_drift_001/candidate_claims.md",
    "examples/skill_tasks/claim_boundary_provider_drift_001/rubric.json",
    "examples/skill_tasks/reproduction_review_001/input.md",
    "examples/skill_tasks/reproduction_review_001/manifest.json",
    "examples/skill_tasks/reproduction_review_001/rubric.json",
    "examples/skill_tasks/reproduction_hash_mismatch_001/input.md",
    "examples/skill_tasks/reproduction_hash_mismatch_001/mismatch_manifest.json",
    "examples/skill_tasks/reproduction_hash_mismatch_001/rubric.json",
    "examples/skill_tasks/plugin_author_001/input.md",
    "examples/skill_tasks/plugin_author_001/rubric.json",
    "examples/skill_tasks/market_rule_plugin_review_001/input.md",
    "examples/skill_tasks/market_rule_plugin_review_001/expected_tests.md",
    "examples/skill_tasks/market_rule_plugin_review_001/rubric.json",
    "examples/skill_task_answers/README.md",
    "examples/skill_task_answers/reference/manifest.json",
    "examples/skill_task_answers/reference/trajectory_audit_001.md",
    "examples/skill_task_answers/reference/intent_execution_autopsy_001.md",
    "examples/skill_task_answers/reference/risk_gate_review_001.md",
    "examples/skill_task_answers/reference/risk_feedback_learning_001.md",
    "examples/skill_task_answers/reference/execution_boundary_001.md",
    "examples/skill_task_answers/reference/execution_attribution_001.md",
    "examples/skill_task_answers/reference/claim_boundary_001.md",
    "examples/skill_task_answers/reference/claim_boundary_provider_drift_001.md",
    "examples/skill_task_answers/reference/reproduction_review_001.md",
    "examples/skill_task_answers/reference/reproduction_hash_mismatch_001.md",
    "examples/skill_task_answers/reference/plugin_author_001.md",
    "examples/skill_task_answers/reference/market_rule_plugin_review_001.md",
    "examples/skill_task_answers/boundary_violation/execution_boundary_001.md",
    "data/real/yahoo_daily_leaderboard_2021_2026/manifest.json",
    "data/public/microstructure_sample/manifest.json",
    "data/public/microstructure_sample/quotes.csv",
    "data/public/microstructure_sample/fills.csv",
    "data/public/binance_btcusdt_perp_2024_03_01_sample/manifest.json",
    "data/public/binance_btcusdt_perp_2024_03_01_sample/quotes.csv",
    "data/public/binance_btcusdt_perp_2024_03_01_sample/fills.csv",
    "notebooks/tradearena_5min_colab.ipynb",
    "plugins/README.md",
    "skills/README.md",
    "skills/skill_template/SKILL.md",
    "skills/tradearena-trajectory-audit/SKILL.md",
    "skills/tradearena-risk-gate-review/SKILL.md",
    "skills/tradearena-execution-calibration/SKILL.md",
    "skills/tradearena-claim-boundary-review/SKILL.md",
    "skills/tradearena-reproduction-review/SKILL.md",
    "skills/tradearena-plugin-author/SKILL.md",
    "scripts/build_skill_index.py",
    "scripts/score_skill_task.py",
    "scripts/score_skill_task_report.py",
    "scripts/validate_skill_contract.py",
    "scripts/run_showcase.py",
    "scripts/run_leaderboard_model_matrix.py",
    "scripts/run_real_market_leaderboard.py",
    "scripts/run_classical_baseline_matrix.py",
    "scripts/build_quality_decomposition.py",
    "scripts/compare_execution_to_fills.py",
    "scripts/calibrate_quote_fill_model.py",
    "scripts/download_binance_microstructure_sample.py",
    "scripts/validate_benchmark_spec.py",
    "scripts/validate_reproduction_report.py",
    "scripts/run_external_reproduction_pack.py",
    "scripts/run_failure_autopsy.py",
    "scripts/validate_benchmark_submission.py",
    "scripts/validate_demo_artifacts.py",
    "SECURITY.md",
]
FORBIDDEN_TRACKED_PATTERNS = [
    "data/llm_cache/*.jsonl",
    "outputs/**/*.json",
    "outputs/**/*.html",
]
PLACEHOLDER_PHRASES = [
    "TODO",
    "TBD",
    "pending labels",
    "insert result",
]
BANNED_PUBLIC_TERMS = [
    "_".join(("trading", "agent", "os")),
]


def main() -> int:
    failures: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            failures.append(f"missing required file: {rel}")

    tracked = _tracked_files()
    for rel in tracked:
        path = ROOT / rel
        if path.is_file() and path.stat().st_size > MAX_TRACKED_FILE_BYTES:
            failures.append(f"tracked file exceeds {MAX_TRACKED_FILE_BYTES} bytes: {rel}")

    for pattern in FORBIDDEN_TRACKED_PATTERNS:
        for match in _git_ls_files(pattern):
            failures.append(f"forbidden tracked artifact: {match}")

    public_text_files = [ROOT / "README.md", ROOT / "docs/results/benchmark_v0_2.md"]
    for path in public_text_files:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for phrase in PLACEHOLDER_PHRASES:
                if phrase.lower() in text:
                    failures.append(f"placeholder phrase '{phrase}' found in {path.relative_to(ROOT)}")

    for rel in tracked:
        path = ROOT / rel
        if path.is_file() and _is_public_text_file(path):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for term in BANNED_PUBLIC_TERMS:
                if term in text:
                    failures.append(f"banned legacy namespace '{term}' found in {rel}")

    if failures:
        print("Release readiness check failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("Release readiness check passed.")
    return 0


def _tracked_files() -> list[str]:
    return _git_ls_files()


def _git_ls_files(pattern: str | None = None) -> list[str]:
    command = ["git", "ls-files"]
    if pattern:
        command.append(pattern)
    result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _is_public_text_file(path: Path) -> bool:
    if path.suffix.lower() not in {".md", ".py", ".toml", ".yml", ".yaml", ".json", ".txt", ".cff"}:
        return False
    parts = set(path.relative_to(ROOT).parts)
    return ".git" not in parts


if __name__ == "__main__":
    raise SystemExit(main())
