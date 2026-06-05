from pathlib import Path

from scripts.check_release_readiness import (
    _check_ci_gate_parity,
    _check_public_identity_boundaries,
    _check_release_candidate_manifest_hashes,
)


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


def test_release_readiness_flags_public_identity_regressions(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    registry = tmp_path / "docs" / "results" / "community_registry.md"
    skill_doc = tmp_path / "docs" / "agent_skills.md"
    pyproject.write_text(
        'description = "LLM-driven trading audit and control system with TradeArena leaderboard artifacts."\n',
        encoding="utf-8",
    )
    registry.parent.mkdir(parents=True)
    registry.write_text("# Community Benchmark Registry\n", encoding="utf-8")
    skill_doc.parent.mkdir(parents=True, exist_ok=True)
    skill_doc.write_text(
        "The task suite measures TradeArena-specific audit ability rather than trading ability:\n",
        encoding="utf-8",
    )

    failures = _check_public_identity_boundaries(
        root=tmp_path,
        tracked_files=[
            "pyproject.toml",
            "docs/results/community_registry.md",
            "docs/agent_skills.md",
        ],
    )

    assert "pyproject.toml must brand the project description as TreLLM" in failures
    assert "legacy public identity phrase 'Community Benchmark Registry' found in docs/results/community_registry.md" in failures
    assert (
        "legacy public identity phrase 'The task suite measures TradeArena-specific audit ability rather than trading ability:' "
        "found in docs/agent_skills.md"
    ) in failures


def test_release_readiness_flags_stale_release_candidate_artifact_hash(tmp_path: Path):
    artifact = tmp_path / "README.md"
    manifest = tmp_path / "docs" / "launch" / "release_candidate_v0.2.1.json"
    artifact.write_text("current artifact text\n", encoding="utf-8")
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        """
{
  "artifact_hashes": [
    {
      "bytes": 1,
      "exists": true,
      "path": "README.md",
      "sha256": "sha256:stale"
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    failures = _check_release_candidate_manifest_hashes(root=tmp_path, manifest_rel="docs/launch/release_candidate_v0.2.1.json")

    assert "release candidate artifact hash mismatch for README.md" in failures
    assert "release candidate artifact byte count mismatch for README.md" in failures
