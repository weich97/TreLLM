from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_external_validation_bundle_summarizes_manifest(tmp_path: Path):
    manifest = {
        "schema": "tradearena_external_reproduction_pack_v1",
        "commit_or_tag": "abc123",
        "git_status_short": "",
        "python": {
            "version": "3.11.0",
            "implementation": "CPython",
            "executable": "python",
            "platform": "Linux-test",
        },
        "commands": [{"id": "release_readiness", "argv": ["python"], "returncode": 0}],
        "artifacts": [{"path": "outputs/examples/audit_report.html", "exists": True, "bytes": 10, "sha256": "sha256:abc"}],
        "trajectory_hash": {"reproducibility_hash": "sha256:def", "file_sha256": "sha256:file"},
        "live_api_used": False,
        "market_data_used": "synthetic",
        "private_fills_used": False,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "bundle.json"
    markdown = tmp_path / "bundle.md"

    subprocess.run(
        [
            sys.executable,
            "scripts/build_external_validation_bundle.py",
            "--manifest",
            str(manifest_path),
            "--output",
            str(output),
            "--markdown-output",
            str(markdown),
            "--environment-label",
            "unit-test",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    bundle = json.loads(output.read_text(encoding="utf-8"))

    assert bundle["issue_ready"] is True
    assert bundle["environment_label"] == "unit-test"
    assert bundle["trajectory_reproducibility_hash"] == "sha256:def"
    assert "Suggested Issue Text" in markdown.read_text(encoding="utf-8")
