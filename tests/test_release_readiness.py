import hashlib
import subprocess
from pathlib import Path

from scripts import build_release_candidate_manifest
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
    schema_doc = tmp_path / "docs" / "schemas.md"
    readme = tmp_path / "README.md"
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
    schema_doc.write_text(
        "# Schemas\n\n"
        "## Community Benchmark Submission Schema\n"
        '"title": "TradeArena Broker Handoff Artifact"\n'
        "Convert TradeArena orders into broker handoff rows.\n"
        "TradeArena is the public leaderboard and benchmark module.\n"
        "Validate that a broker approval artifact binds to a handoff artifact.\n"
        "Run TradeArena experiments.\n"
        "Replay one step from a TradeArena trajectory JSON.\n"
        "Export a TradeArena trajectory to a local trace JSON.\n"
        "Create a local TradeArena plugin skeleton.\n"
        "strengthen TradeArena's execution evidence.\n"
        "the TradeArena calibration pipeline was run.\n"
        "unless recorded in the TradeArena run manifest.\n",
        encoding="utf-8",
    )
    readme.write_text(
        "The current public benchmark path runs offline and paper/sandbox experiments.\n"
        "Before calling TradeArena an externally validated community benchmark, more evidence is required.\n",
        encoding="utf-8",
    )

    failures = _check_public_identity_boundaries(
        root=tmp_path,
        tracked_files=[
            "pyproject.toml",
            "docs/results/community_registry.md",
            "docs/agent_skills.md",
            "docs/schemas.md",
            "README.md",
        ],
    )

    assert "pyproject.toml must brand the project description as TreLLM" in failures
    assert "legacy public identity phrase 'Community Benchmark Registry' found in docs/results/community_registry.md" in failures
    assert (
        "legacy public identity phrase 'The task suite measures TradeArena-specific audit ability rather than trading ability:' "
        "found in docs/agent_skills.md"
    ) in failures
    assert "legacy public identity phrase 'The current public benchmark path' found in README.md" in failures
    assert (
        "legacy public identity phrase 'Before calling TradeArena an externally validated community benchmark' "
        "found in README.md"
    ) in failures
    assert "legacy public identity phrase 'Community Benchmark Submission Schema' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'TradeArena Broker Handoff Artifact' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Convert TradeArena orders into broker handoff rows.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'TradeArena is the public leaderboard and benchmark module' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Validate that a broker approval artifact binds to a handoff artifact.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Run TradeArena experiments.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Replay one step from a TradeArena trajectory JSON.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Export a TradeArena trajectory to a local trace JSON.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Create a local TradeArena plugin skeleton.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'strengthen TradeArena's execution evidence' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'the TradeArena calibration pipeline was run' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'unless recorded in the TradeArena run manifest.' found in docs/schemas.md" in failures


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


def test_release_readiness_uses_git_blob_bytes_for_manifest_artifacts(tmp_path: Path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)

    artifact = tmp_path / "README.md"
    manifest = tmp_path / "docs" / "launch" / "release_candidate_v0.2.1.json"
    artifact.write_bytes(b"line one\nline two\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "Add artifact"], cwd=tmp_path, check=True, capture_output=True, text=True)

    artifact.write_bytes(b"line one\r\nline two\r\n")
    digest = "sha256:" + hashlib.sha256(b"line one\nline two\n").hexdigest()
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        f"""
{{
  "artifact_hashes": [
    {{
      "bytes": 18,
      "exists": true,
      "path": "README.md",
      "sha256": "{digest}"
    }}
  ]
}}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    failures = _check_release_candidate_manifest_hashes(root=tmp_path, manifest_rel="docs/launch/release_candidate_v0.2.1.json")

    assert failures == []


def test_release_readiness_uses_canonical_worktree_bytes_for_dirty_manifest_artifacts(tmp_path: Path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)

    artifact = tmp_path / "README.md"
    manifest = tmp_path / "docs" / "launch" / "release_candidate_v0.2.1.json"
    artifact.write_bytes(b"old line\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "Add artifact"], cwd=tmp_path, check=True, capture_output=True, text=True)

    current_bytes = b"new line\n"
    artifact.write_bytes(b"new line\r\n")
    digest = "sha256:" + hashlib.sha256(current_bytes).hexdigest()
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        f"""
{{
  "artifact_hashes": [
    {{
      "bytes": {len(current_bytes)},
      "exists": true,
      "path": "README.md",
      "sha256": "{digest}"
    }}
  ]
}}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    failures = _check_release_candidate_manifest_hashes(root=tmp_path, manifest_rel="docs/launch/release_candidate_v0.2.1.json")

    assert failures == []


def test_release_candidate_manifest_builder_uses_git_blob_bytes(tmp_path: Path, monkeypatch):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)

    artifact = tmp_path / "README.md"
    artifact.write_bytes(b"line one\nline two\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "Add artifact"], cwd=tmp_path, check=True, capture_output=True, text=True)
    artifact.write_bytes(b"line one\r\nline two\r\n")

    monkeypatch.setattr(build_release_candidate_manifest, "ROOT", tmp_path)

    artifact_hash = build_release_candidate_manifest._artifact_hash("README.md")

    assert artifact_hash["bytes"] == 18
    assert artifact_hash["sha256"] == "sha256:" + hashlib.sha256(b"line one\nline two\n").hexdigest()


def test_release_candidate_manifest_builder_uses_canonical_worktree_bytes_when_dirty(tmp_path: Path, monkeypatch):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)

    artifact = tmp_path / "README.md"
    artifact.write_bytes(b"old line\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "Add artifact"], cwd=tmp_path, check=True, capture_output=True, text=True)
    artifact.write_bytes(b"new line\r\n")

    monkeypatch.setattr(build_release_candidate_manifest, "ROOT", tmp_path)

    artifact_hash = build_release_candidate_manifest._artifact_hash("README.md")

    assert artifact_hash["bytes"] == len(b"new line\n")
    assert artifact_hash["sha256"] == "sha256:" + hashlib.sha256(b"new line\n").hexdigest()
