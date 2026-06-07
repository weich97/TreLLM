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
        "TradeArena benchmark module.\n"
        "Validate that a broker approval artifact binds to a handoff artifact.\n"
        "Run TradeArena experiments.\n"
        "Replay one step from a TradeArena trajectory JSON.\n"
        "Export a TradeArena trajectory to a local trace JSON.\n"
        "Create a local TradeArena plugin skeleton.\n"
        "strengthen TradeArena's execution evidence.\n"
        "the TradeArena calibration pipeline was run.\n"
        "unless recorded in the TradeArena run manifest.\n"
        "Convert approved TradeArena orders into broker-review files.\n"
        "TradeArena's compact execution equation.\n"
        "TradeArena execution-stress equation.\n"
        "upgrades TradeArena from an OHLCV-only smoke test.\n"
        "TradeArena Replay:\n"
        "| TradeArena record | OpenTelemetry-style span | Evals or trace-style field |\n"
        "TradeArena's default `market_impact` coefficient.\n"
        "claiming that TradeArena explains realized transaction costs.\n"
        "TradeArena strategy interface and downstream risk/execution/evaluation stack.\n"
        "The framework is the experimental substrate.\n"
        "This makes the framework relevant to LLM trading agents.\n"
        "one runnable example for each framework surface.\n"
        "keeping the framework auditable.\n"
        "Extend the framework with small, reviewable plugins.\n"
        "reusing the rest of the framework.\n"
        "One new plugin, the rest of the framework stays fixed.\n"
        "core framework experiment axes.\n"
        "four framework axes.\n"
        "This makes the framework useful alongside stronger forecasting.\n"
        "The current public repository is strongest at the prototype and early benchmark levels.\n"
        "For the staged path from benchmark research to supervised live execution.\n"
        "These contributions move TreLLM from benchmark research toward human-gated.\n"
        'framework: str = "TradeArena"\n'
        '"title": "TradeArena trajectory"\n'
        '"title": "TradeArena execution calibration profile"\n'
        '"title": "TradeArena Demo Artifact Contract"\n'
        '"title": "TradeArena External Reproduction Report"\n'
        '"title": "TradeArena skill task answer set"\n'
        '"title": "TradeArena skill task rubric"\n'
        '"User-Agent": "TradeArena-calibration-sample"\n'
        '"User-Agent": "TradeArena mirror downloader"\n'
        "Volume is normalized to TradeArena units\n"
        "# TradeArena v0.2 External Reproduction Pack\n",
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
    assert "legacy public identity phrase 'TradeArena benchmark module' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Validate that a broker approval artifact binds to a handoff artifact.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Run TradeArena experiments.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Replay one step from a TradeArena trajectory JSON.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Export a TradeArena trajectory to a local trace JSON.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Create a local TradeArena plugin skeleton.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'strengthen TradeArena's execution evidence' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'the TradeArena calibration pipeline was run' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'unless recorded in the TradeArena run manifest.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'Convert approved TradeArena orders into broker-review files.' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'TradeArena's compact execution equation' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'TradeArena execution-stress equation' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'upgrades TradeArena from an OHLCV-only smoke test' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'TradeArena Replay:' found in docs/schemas.md" in failures
    assert (
        "legacy public identity phrase '| TradeArena record | OpenTelemetry-style span | Evals or trace-style field |' "
        "found in docs/schemas.md"
    ) in failures
    assert "legacy public identity phrase 'TradeArena's default `market_impact` coefficient' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'claiming that TradeArena explains realized transaction costs' found in docs/schemas.md" in failures
    assert (
        "legacy public identity phrase 'TradeArena strategy interface and downstream risk/execution/evaluation stack.' "
        "found in docs/schemas.md"
    ) in failures
    assert "legacy public identity phrase 'The framework is the experimental substrate' found in docs/schemas.md" in failures
    assert (
        "legacy public identity phrase 'This makes the framework relevant to LLM trading agents' found in docs/schemas.md"
        in failures
    )
    assert (
        "legacy public identity phrase 'one runnable example for each framework surface' found in docs/schemas.md"
        in failures
    )
    assert "legacy public identity phrase 'keeping the framework auditable' found in docs/schemas.md" in failures
    assert (
        "legacy public identity phrase 'Extend the framework with small, reviewable plugins.' found in docs/schemas.md"
        in failures
    )
    assert "legacy public identity phrase 'reusing the rest of the framework.' found in docs/schemas.md" in failures
    assert (
        "legacy public identity phrase 'One new plugin, the rest of the framework stays fixed' found in docs/schemas.md"
        in failures
    )
    assert "legacy public identity phrase 'core framework experiment axes' found in docs/schemas.md" in failures
    assert "legacy public identity phrase 'four framework axes' found in docs/schemas.md" in failures
    assert (
        "legacy public identity phrase 'This makes the framework useful alongside stronger forecasting' found in docs/schemas.md"
        in failures
    )
    assert (
        "legacy public identity phrase 'The current public repository is strongest at the prototype and early benchmark levels' "
        "found in docs/schemas.md"
    ) in failures
    assert (
        "legacy public identity phrase 'For the staged path from benchmark research to supervised live execution' "
        "found in docs/schemas.md"
    ) in failures
    assert (
        "legacy public identity phrase 'These contributions move TreLLM from benchmark research toward human-gated' "
        "found in docs/schemas.md"
    ) in failures
    assert 'legacy public identity phrase \'framework: str = "TradeArena"\' found in docs/schemas.md' in failures
    for title in [
        "TradeArena trajectory",
        "TradeArena execution calibration profile",
        "TradeArena Demo Artifact Contract",
        "TradeArena External Reproduction Report",
        "TradeArena skill task answer set",
        "TradeArena skill task rubric",
    ]:
        assert f"legacy public identity phrase '\"title\": \"{title}\"' found in docs/schemas.md" in failures
    assert 'legacy public identity phrase \'"User-Agent": "TradeArena-calibration-sample"\' found in docs/schemas.md' in failures
    assert 'legacy public identity phrase \'"User-Agent": "TradeArena mirror downloader"\' found in docs/schemas.md' in failures
    assert "legacy public identity phrase 'Volume is normalized to TradeArena units' found in docs/schemas.md" in failures
    assert "legacy public identity phrase '# TradeArena v0.2 External Reproduction Pack' found in docs/schemas.md" in failures


def test_release_readiness_flags_stale_public_repository_locations(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "\n".join(
            [
                "Clone from https://github.com/weich97/TradeArena.git",
                "Open https://weich97.github.io/TradeArena/",
                "Launch https://colab.research.google.com/github/weich97/TradeArena/blob/main/notebook.ipynb",
                "Then run cd TradeArena",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    failures = _check_public_identity_boundaries(root=tmp_path, tracked_files=["README.md"])

    assert "stale public repository location 'github.com/weich97/TradeArena' found in README.md" in failures
    assert "stale public repository location 'github.io/TradeArena' found in README.md" in failures
    assert "stale public repository location 'cd TradeArena' found in README.md" in failures


def test_release_readiness_requires_current_trellm_repository_locations(tmp_path: Path):
    citation = tmp_path / "CITATION.cff"
    schema = tmp_path / "schemas" / "trajectory.schema.json"
    notebook = tmp_path / "notebooks" / "tradearena_5min_colab.ipynb"
    citation.write_text(
        'repository-code: "https://github.com/weich97/TreLLM-archive"\nurl: "https://github.com/weich97/TreLLM-archive"\n',
        encoding="utf-8",
    )
    schema.parent.mkdir(parents=True)
    schema.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://example.com/schemas/trajectory.schema.json"}\n',
        encoding="utf-8",
    )
    notebook.parent.mkdir(parents=True)
    notebook.write_text(
        '{"cells": [{"source": ["!git clone https://github.com/weich97/TreLLM-archive.git\\n", "os.chdir(\\"TreLLM-archive\\")\\n"]}]}\n',
        encoding="utf-8",
    )

    failures = _check_public_identity_boundaries(
        root=tmp_path,
        tracked_files=[
            "CITATION.cff",
            "schemas/trajectory.schema.json",
            "notebooks/tradearena_5min_colab.ipynb",
        ],
    )

    assert (
        "required public repository location missing from CITATION.cff: "
        'repository-code: "https://github.com/weich97/TreLLM"'
    ) in failures
    assert (
        "required public repository location missing from schemas/trajectory.schema.json: "
        "https://github.com/weich97/TreLLM/schemas/"
    ) in failures
    assert (
        "required public repository location missing from notebooks/tradearena_5min_colab.ipynb: "
        "git clone https://github.com/weich97/TreLLM.git"
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
