# Broker Adapter Contract

This contract defines the minimum bar for any TradeArena adapter that touches a
broker, exchange, paper account, or order-management workflow. It applies to
offline exports, paper trading sandboxes, and future human-approved live
adapters.

The contract is intentionally stricter than the current public examples. A
small adapter that cannot satisfy these rules should stay as an offline export.

## Modes

Every broker adapter must declare exactly one mode at runtime:

| Mode | Broker API call allowed? | Live order allowed? | Typical use |
| --- | --- | --- | --- |
| `offline_export` | No | No | Write CSV/JSON orders for review. |
| `dry_run` | No | No | Validate request shape without network calls. |
| `paper_sandbox` | Yes, paper account only | No | Submit to a broker simulator or paper account. |
| `live_human_approved` | Yes | Only after explicit approval | Submit constrained live orders after operator review. |

The default mode must be `offline_export` or `dry_run`. `live_human_approved`
must never be the default.

The current code-level primitives live in `tradearena.tools.broker_export`:

- `BrokerAdapter`, the minimal interface future broker adapters should satisfy;
- `BrokerAdapterMode`;
- `BrokerSafetyConfig`;
- `BrokerApproval`;
- `BrokerAdapterContractError`;
- `BrokerOrderStatus`;
- `BrokerResponse`;
- `BrokerReconciliationSummary`;
- `build_broker_approval_artifact`;
- `broker_approval_from_artifact`;
- `broker_safety_from_approval_artifact`;
- `reconcile_broker_responses`;
- `validate_broker_approval_artifact`;
- `validate_broker_approval_artifact_file`;
- `validate_broker_handoff_artifact`;
- `validate_broker_handoff_artifact_file`;
- `validate_broker_response_artifact`;
- `validate_broker_response_artifact_file`;
- `write_broker_response_artifact`;
- `DryRunBrokerAdapter`, the no-network reference adapter for request-shape
  validation;
- `AlpacaPaperExportAdapter`, the export-only reference implementation.

## Required Order Fields

Each broker handoff row should include:

- `client_order_id`;
- `symbol`;
- `side`;
- `order_type`;
- `quantity`;
- `time_in_force`;
- `limit_price` when relevant;
- `risk_report_id` or risk report hash;
- `trajectory_id` or run hash;
- `approval_status`;
- `approved_by` when live submission is allowed;
- `approved_at` when live submission is allowed;
- `submit_live`;
- `reason`;
- `max_notional`;
- `account_mode`.

Current export-only examples may use a subset, but new broker-facing adapters
should move toward this complete shape.
Public handoff artifacts should validate against
[`../schemas/broker_handoff_artifact.schema.json`](../schemas/broker_handoff_artifact.schema.json).
Use `tradearena validate-broker-handoff <artifact.json>` before sharing a
broker-review or paper-sandbox request artifact.

## Safety Invariants

Adapter implementations must satisfy these invariants:

- default construction cannot submit a live order;
- `submit_live=true` is rejected unless mode is `live_human_approved`;
- live mode requires an explicit approval record;
- live mode requires max notional and max quantity limits;
- live mode must have a reference price whenever max-notional checks are
  enforced;
- live orders must satisfy both the adapter max-notional limit and the human
  approval max-notional limit;
- allowed symbols and allowed order types are enforced before broker handoff;
- broker credentials are read from environment variables or an OS secret
  manager, never from committed files or command-line arguments;
- logs and exceptions redact credentials, account numbers, and private holdings;
- all generated artifacts state whether they are offline, paper, or live;
- tests prove that offline and dry-run modes perform no broker API calls.

## Broker Response Artifact

Any adapter that calls a broker API should write a response artifact with:

- request client order ID;
- broker order ID when available;
- submitted quantity and accepted quantity;
- status: accepted, rejected, partially filled, filled, canceled, expired, or
  unknown;
- rejection reason or error class with sensitive fields redacted;
- submitted timestamp and broker timestamp;
- fill price, fill quantity, fees, and liquidity flags when available;
- account mode: paper or live;
- reconciliation status against the original TradeArena order.

This artifact is part of the audit trail, not a throwaway log.
`write_broker_response_artifact(...)` writes the repository's first version of
this artifact. It records `tradearena_broker_response_artifact_v0.1`, the
adapter mode, account mode, response rows, and a reconciliation summary with
missing and unmatched response counts.
Public response artifacts should validate against
[`../schemas/broker_response_artifact.schema.json`](../schemas/broker_response_artifact.schema.json).
Use `tradearena validate-broker-response <artifact.json>` before submitting a
broker-facing PR or paper-sandbox run report.

## Human Approval Gate

`live_human_approved` mode requires a durable approval record:

```json
{
  "schema": "tradearena_broker_approval_artifact_v0.1",
  "approval_id": "approval-20260531-001",
  "approval_status": "approved",
  "approved_by": "operator-id",
  "approved_at": "2026-05-31T12:00:00Z",
  "expires_at": "2026-05-31T13:00:00Z",
  "account_mode": "live",
  "max_notional": 1000.0,
  "max_quantity": 10.0,
  "allowed_symbols": ["AAPL", "MSFT"],
  "allowed_order_types": ["market", "limit"],
  "approval_reason": "paper/live shadow checks passed for this rebalance",
  "request_artifact_hash": "sha256:..."
}
```

The adapter should reject stale, missing, or over-broad approvals. Approval
records should use redacted operator IDs in public artifacts and can be checked
with `tradearena validate-broker-approval <artifact.json>`.
Adapter implementations can turn a validated approval artifact into the
runtime safety gate with `broker_safety_from_approval_artifact(...)`; the
result is a `BrokerSafetyConfig` in `live_human_approved` mode with the same
symbol, order-type, quantity, and notional limits as the approval.
Pass `now=` when validating or consuming approval artifacts so stale approvals
are rejected before any live-mode safety config is created.

## Testing Requirements

At minimum, a broker adapter PR should include tests that prove:

- default mode writes an offline artifact and makes no network call;
- dry-run mode validates request shape and writes a broker handoff artifact
  without broker credentials or API calls;
- live submission is rejected without approval;
- order-size and symbol allow-list checks run before broker handoff;
- credentials are not printed in errors;
- response artifacts can represent rejected and partially filled orders;
- a kill-switch setting blocks all broker submission paths.

The current Alpaca example is intentionally below live-adapter scope: it writes
broker-review JSON/CSV files by default, declares `adapter_mode=offline_export`,
and sets `submit_live=false`.
