# Live Trading Readiness

TradeArena should grow beyond a paper-only benchmark, but it should not jump
straight from benchmark rows to unattended live orders. The intended direction
is **live-ready, human-gated trading infrastructure**: every order candidate is
observable, risk-checked, calibrated, exported, approved, reconciled, and
auditable before any broker-facing adapter can submit it.

The default repository path remains safe: first-run commands do not place live
orders or require broker credentials. The long-term value is that the same
audit stack can become the control plane around real trading systems.

## Maturity Ladder

| Stage | Name | What TradeArena can do | Required evidence before moving on |
| --- | --- | --- | --- |
| 0 | Offline benchmark | Run deterministic agents, risk gates, and stress execution without network calls. | Reproducible trajectory, schema validation, release-readiness checks. |
| 1 | Calibrated paper research | Fit or replay execution assumptions from quote, order-book, or fill evidence. | Calibration report with source, venue, date range, residuals, and hashes. |
| 2 | Broker-review export | Convert approved paper orders into broker-compatible review files. | `submit_live=false`, human approval fields, redacted artifacts, no broker API call. |
| 3 | Paper trading sandbox | Submit to a broker sandbox or paper account only. | Sandbox credentials, account isolation, order limits, dry-run test, audit manifest. |
| 4 | Human-approved live adapter | Submit live orders only after explicit operator approval. | Broker adapter contract, manual approval record, kill switch, reconciliation, incident runbook. |
| 5 | Supervised automation | Allow tightly scoped automation after repeated paper/live shadow validation. | External review, capital limits, monitoring, rollback, compliance and jurisdiction review. |

Stages 4 and 5 are not part of the public benchmark claim. They are future
integration tracks for users who accept the regulatory, operational, and
financial risk of real trading.

## Live-Ready Architecture

The system should keep these boundaries separate:

| Layer | Responsibility | Current surface |
| --- | --- | --- |
| Decision | Agents, strategies, and planners propose intent. | `tradearena.agents`, `tradearena.planning` |
| Risk gate | Risk managers clip, block, or annotate intent. | `MaxPositionRiskManager`, market-rule helpers |
| Execution model | Simulators, quote replay, fill replay, and calibration estimate feasibility. | `tradearena.execution` |
| Broker handoff | Broker adapters export or submit only approved orders. | `AlpacaPaperExportAdapter` |
| Reconciliation | Fills, rejects, partial fills, and broker state are compared against intent. | future broker adapter reports |
| Audit trail | Trajectory, risk report, order review, broker response, and hashes stay linked. | trajectory records, manifests, registry |

A broker-facing adapter should never bypass the decision/risk/execution trail.
It consumes approved orders and produces a broker handoff artifact or a broker
response artifact.

## Stage Gate Checklist

Before a broker-facing contribution is accepted, it should prove:

- default mode is `offline_export`, `dry_run`, or `paper_sandbox`;
- live submission is impossible without an explicit mode switch;
- credentials are read from environment variables or an OS secret manager;
- no credentials, account IDs, private holdings, raw fills, or raw provider
  responses are committed;
- every order carries a risk report reference, approval status, and client
  order ID;
- max notional, max quantity, allowed symbols, and allowed order types are
  enforced before broker handoff;
- cancellation, partial-fill, rejection, and reconciliation states are
  represented in artifacts;
- a kill-switch or disable flag can block all broker submission paths;
- tests prove that the default path cannot submit live orders;
- docs name the account type: offline, paper sandbox, or live human-approved.

## Recommended Contribution Sequence

1. Harden export-only broker handoff files and review manifests.
2. Add a generic `BrokerAdapter` interface with `dry_run` and `paper_sandbox`
   modes.
3. Add one broker-specific sandbox adapter behind an optional dependency.
4. Add reconciliation reports that compare submitted orders, broker acks, fills,
   cancels, rejects, and portfolio state.
5. Add human approval records and operator runbooks.
6. Only then discuss constrained live submission, and keep it out of first-run
   examples.

The next engineering step is the generic broker adapter contract in
[`broker_adapter_contract.md`](broker_adapter_contract.md).
