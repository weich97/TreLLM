from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradearena.core.domain import Order, OrderType, Side
from tradearena.core.serialization import write_json
from tradearena.tools import (
    BrokerAdapterContractError,
    BrokerApproval,
    broker_safety_from_approval_artifact,
    build_broker_approval_artifact,
    validate_broker_approval_artifact,
)

OUTPUT_DIR = Path("outputs/examples/broker_approval_safety")


def main() -> int:
    approval = BrokerApproval(
        approval_status="approved",
        approved_by="operator-demo-7",
        approved_at="2026-05-31T12:00:00Z",
        max_notional=250.0,
        allowed_symbols=("AAPL", "MSFT"),
        approval_reason="paper shadow checks passed for this bounded rebalance",
    )
    artifact = build_broker_approval_artifact(
        approval,
        approval_id="approval-demo-001",
        account_mode="live",
        max_quantity=5.0,
        allowed_order_types=(OrderType.LIMIT,),
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash="sha256:demo-redacted-request-hash",
    )
    demo_now = "2026-05-31T12:30:00Z"
    validation_errors = validate_broker_approval_artifact(artifact, now=demo_now)
    safety = broker_safety_from_approval_artifact(artifact, now=demo_now)

    approved_order_passed = False
    oversized_order_blocked = False
    blocked_reason = ""
    safety.validate_order(
        Order("AAPL", Side.BUY, 2.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="approved demo order"),
        reference_price=100.0,
    )
    approved_order_passed = True
    try:
        safety.validate_order(
            Order("AAPL", Side.BUY, 3.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="oversized demo order"),
            reference_price=100.0,
        )
    except BrokerAdapterContractError as exc:
        oversized_order_blocked = True
        blocked_reason = str(exc)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = OUTPUT_DIR / "broker_approval_artifact.json"
    artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "approval_id": artifact["approval_id"],
        "approval_validated": not validation_errors,
        "approval_checked_at": demo_now,
        "validation_errors": validation_errors,
        "adapter_mode": safety.mode.value,
        "account_mode": safety.account_mode,
        "allowed_symbols": list(safety.allowed_symbols),
        "allowed_order_types": [order_type.value for order_type in safety.allowed_order_types],
        "max_notional": safety.max_notional,
        "max_quantity": safety.max_quantity,
        "approved_order_passed": approved_order_passed,
        "oversized_order_blocked": oversized_order_blocked,
        "blocked_reason": blocked_reason,
        "safety_note": "Approval artifact is redacted and local-only; no broker credentials are read and no orders are submitted.",
    }
    write_json(OUTPUT_DIR / "summary.json", summary)
    print("Broker approval safety demo")
    print(f"  approval_validated={summary['approval_validated']}")
    print(f"  approved_order_passed={approved_order_passed}")
    print(f"  oversized_order_blocked={oversized_order_blocked}")
    print(f"  wrote={artifact_path}")
    return 0 if not validation_errors and approved_order_passed and oversized_order_blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
