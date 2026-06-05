from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradearena.core.serialization import write_json
from tradearena.tools import validate_live_readiness_preflight_bundle_file

OUTPUT_DIR = Path("outputs/examples/live_readiness_preflight")
BUNDLE_PATH = OUTPUT_DIR / "preflight_bundle.json"
SUMMARY_PATH = OUTPUT_DIR / "preflight_summary.json"
DEMO_NOW = "2026-05-31T12:30:00Z"


def main() -> int:
    for command in (
        [sys.executable, "examples/broker_capability_manifest_demo.py"],
        [sys.executable, "examples/broker_approval_safety_demo.py"],
        [sys.executable, "examples/broker_response_reconciliation_demo.py"],
        [sys.executable, "examples/operator_runbook_demo.py"],
    ):
        subprocess.run(command, cwd=ROOT, check=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bundle = {
        "schema": "trellm_live_readiness_preflight_v0.1",
        "capability_manifest": "outputs/examples/broker_capability_manifest/capability_manifest.json",
        "handoff_artifact": "outputs/examples/broker_approval_safety/dry_run_orders.json",
        "approval_artifact": "outputs/examples/broker_approval_safety/broker_approval_artifact.json",
        "response_artifact": "outputs/examples/broker_response_reconciliation/broker_response_artifact.json",
        "operator_runbook_artifact": "outputs/examples/operator_runbook/summary.json",
        "approval_checked_at": DEMO_NOW,
        "safety_note": (
            "This preflight bundle links offline and paper artifacts for review. "
            "It performs no broker API calls and does not authorize live submission."
        ),
    }
    write_json(BUNDLE_PATH, bundle)
    summary, errors = validate_live_readiness_preflight_bundle_file(BUNDLE_PATH, now=DEMO_NOW)
    write_json(SUMMARY_PATH, summary)
    print("Live-readiness preflight demo")
    print(f"  ready={summary['ready']}")
    print(f"  error_count={summary['error_count']}")
    print(f"  wrote={BUNDLE_PATH}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
