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


if __name__ == "__main__":
    raise SystemExit(main())
