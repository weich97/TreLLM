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

- `BrokerAdapterMode`;
- `BrokerSafetyConfig`;
- `BrokerApproval`;
- `BrokerAdapterContractError`;
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

## Safety Invariants

Adapter implementations must satisfy these invariants:

- default construction cannot submit a live order;
- `submit_live=true` is rejected unless mode is `live_human_approved`;
- live mode requires an explicit approval record;
- live mode requires max notional and max quantity limits;
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

## Human Approval Gate

`live_human_approved` mode requires a durable approval record:

```json
{
  "approval_status": "approved",
  "approved_by": "operator-id",
  "approved_at": "2026-05-31T12:00:00Z",
  "max_notional": 1000.0,
  "allowed_symbols": ["AAPL", "MSFT"],
  "approval_reason": "paper/live shadow checks passed for this rebalance"
}
```

The adapter should reject stale, missing, or over-broad approvals. Approval
records should be kept out of public artifacts when they expose account or
operator identity.

## Testing Requirements

At minimum, a broker adapter PR should include tests that prove:

- default mode writes an offline artifact and makes no network call;
- live submission is rejected without approval;
- order-size and symbol allow-list checks run before broker handoff;
- credentials are not printed in errors;
- response artifacts can represent rejected and partially filled orders;
- a kill-switch setting blocks all broker submission paths.

The current Alpaca example is intentionally below live-adapter scope: it writes
broker-review JSON/CSV files by default, declares `adapter_mode=offline_export`,
and sets `submit_live=false`.
