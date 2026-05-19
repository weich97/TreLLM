from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_FILE_BYTES = 25 * 1024 * 1024
REQUIRED_FILES = [
    "README.md",
    "CITATION.cff",
    "docs/getting_started.md",
    "docs/advanced_integrations_security.md",
    "docs/technical_report.md",
    "docs/benchmark_maturity.md",
    "docs/academic_report_plan.md",
    "docs/external_validation.md",
    "docs/community_participation.md",
    "docs/community_tasks.md",
    "docs/community_operations.md",
    "docs/plugin_development.md",
    "docs/benchmark_challenges.md",
    "docs/market_rules.md",
    "docs/observability.md",
    "docs/artifact_portability.md",
    "docs/demo_matrix.md",
    "docs/results/benchmark_v0_1.md",
    "docs/results/llm_live_baseline.md",
    "docs/results/llm_live_baseline.json",
    "docs/results/llm_live_baseline_manifest/manifest.json",
    "docs/results/llm_live_baseline_manifest/poe_gpt55_live_smoke_2026-05-18_summary.json",
    "docs/results/community_registry.md",
    "docs/results/community_registry.html",
    "docs/demo_artifacts.yaml",
    "schemas/benchmark_submission.schema.json",
    "schemas/demo_artifact_contract.schema.json",
    "examples/benchmark_submissions/example_redacted_submission.json",
    "notebooks/tradearena_5min_colab.ipynb",
    "plugins/README.md",
    "scripts/run_showcase.py",
    "scripts/compare_execution_to_fills.py",
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

    public_text_files = [ROOT / "README.md", ROOT / "docs/results/benchmark_v0_1.md"]
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
