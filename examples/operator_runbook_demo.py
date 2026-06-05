from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradearena.core.serialization import write_json

OUTPUT_DIR = Path("outputs/examples/operator_runbook")
SUMMARY_PATH = OUTPUT_DIR / "summary.json"
RUNBOOK_PATH = OUTPUT_DIR / "operator_runbook.md"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checklist = [
        {
            "id": "mode-boundary",
            "owner": "operator",
            "evidence": "adapter mode recorded as offline_export, dry_run, paper_sandbox, or live_human_approved",
            "pass_condition": "default path cannot submit live orders",
        },
        {
            "id": "approval-expiry",
            "owner": "operator",
            "evidence": "broker approval artifact with approved_at, expires_at, max_notional, max_quantity, and request hash",
            "pass_condition": "approval is unexpired and bound to the reviewed handoff artifact",
        },
        {
            "id": "kill-switch",
            "owner": "operator",
            "evidence": "kill switch flag or disable control checked before handoff",
            "pass_condition": "tripped kill switch blocks every broker-facing path",
        },
        {
            "id": "reconciliation",
            "owner": "reviewer",
            "evidence": "broker response artifact with status counts, missing responses, unmatched responses, and redacted reasons",
            "pass_condition": "reconciliation summary validates against response rows",
        },
        {
            "id": "rollback",
            "owner": "operator",
            "evidence": "rollback owner, account mode, affected symbols, and artifact retention path are named",
            "pass_condition": "operator can disable submission and preserve the audit bundle",
        },
    ]
    summary = {
        "schema": "trellm_operator_runbook_v0.1",
        "live_submission": False,
        "default_mode": "offline_export",
        "allowed_modes": ["offline_export", "dry_run", "paper_sandbox", "live_human_approved"],
        "manual_approval_required": True,
        "kill_switch_required": True,
        "approval_expiry_required": True,
        "artifact_retention_required": True,
        "incident_owner_required": True,
        "checklist": checklist,
        "verification_commands": [
            "python examples/operator_runbook_demo.py",
            "tradearena validate-operator-runbook outputs/examples/operator_runbook/summary.json",
            "python scripts/validate_demo_artifacts.py",
        ],
        "safety_note": (
            "This runbook is an offline planning artifact. It reads no credentials, "
            "calls no broker API, and does not authorize live submission."
        ),
    }
    write_json(SUMMARY_PATH, summary)
    RUNBOOK_PATH.write_text(_render_runbook(summary), encoding="utf-8")
    print("Operator runbook demo")
    print(f"  checklist_items={len(checklist)}")
    print(f"  live_submission={summary['live_submission']}")
    print(f"  wrote={RUNBOOK_PATH}")
    return 0


def _render_runbook(summary: dict) -> str:
    lines = [
        "# TreLLM Operator Runbook Checklist",
        "",
        "This offline artifact shows the human-gated controls a live-capable path must name before it can be reviewed.",
        "It is not a broker adapter and it does not authorize live submission.",
        "",
        "## Boundary",
        "",
        f"- Default mode: `{summary['default_mode']}`",
        f"- Live submission in this demo: `{str(summary['live_submission']).lower()}`",
        "- Manual approval required: `true`",
        "- Kill switch required: `true`",
        "- Approval expiry required: `true`",
        "- Artifact retention required: `true`",
        "",
        "## Checklist",
        "",
        "| ID | Owner | Evidence | Pass condition |",
        "| --- | --- | --- | --- |",
    ]
    for item in summary["checklist"]:
        lines.append(f"| `{item['id']}` | {item['owner']} | {item['evidence']} | {item['pass_condition']} |")
    lines.extend(
        [
            "",
            "## Incident Response",
            "",
            "1. Trip the kill switch or disable flag before creating any broker-facing artifact.",
            "2. Preserve the reviewed handoff, approval artifact, response artifact, and command transcript.",
            "3. Reconcile broker-visible statuses against TreLLM client order IDs.",
            "4. Record the incident owner, affected account mode, affected symbols, and rollback decision.",
            "5. Re-enable only after a new approval artifact and reviewed request hash are created.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
