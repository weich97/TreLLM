# TradeArena Schemas

TradeArena treats a financial AI agent as an auditable reliability lifecycle,
not a black-box signal generator. A benchmark step records the following
protocol surfaces.

## Observation Schema

- `timestamp`
- `bars`: symbol to OHLCV bar
- `news`: timestamped news items
- `macro`: macro observations
- `filings`: optional timestamped filing items loaded from CSV sidecars
- `alt_data`: optional alternative data
- `portfolio_state`: cash, positions, prices, equity
- `memory_digest`: hash of recent memory state

## Action Schema

- `Decision`: symbol, side, target weight, confidence, rationale
- `Order`: symbol, side, quantity, type, limit price, reason
- `Fill`: executed quantity, requested quantity, price, commission, slippage, latency, liquidity, fill ratio, status
- execution config: commission, quoted spread, base slippage, latency,
  participation, and market impact assumptions

## Risk Schema

- `RiskBudget`: position weight, gross exposure, turnover, drawdown, participation, confidence, latency, slippage limits
- `RiskCheck`: named constraint check with pass/fail, severity, message
- `RiskViolation`: phase, constraint, observed value, limit, severity, symbol
- `RiskReport`: phase-level audit object for pre-trade, in-trade, and post-trade stages
- drawdown kill-switch metadata: rolling drawdown, lookback window, de-risk
  weight, and trigger status
- `RiskAttribution`: post-trade PnL/cost/exposure attribution

## Memory Schema

- append-only events
- trade journal entries
- thesis tracking
- failure cases
- digest for reproducibility checks
- memory-aware strategy diagnostics: configured `memory_decay_rate`, weighted
  `memory_pollution_ratio`, base and memory-adjusted target weights, and
  `memory_driven_leverage_amplification`

## Tool Schema

- `ToolCallRecord`: tool name, inputs, outputs, timestamp, status
- examples: analyst stack, feature store, risk calculator, optimizer, backtester, retrieval

## Trajectory Schema

Each step records:

- `reproducibility_state`
- `agent_trace`
- observation
- signals
- decisions
- approved decisions
- pre-trade risk report
- orders
- fills
- execution report
- in-trade risk report
- post-trade risk attribution report
- risk violations
- portfolio
- memory events

## Evaluation Schema

- performance: return, volatility, Sharpe, drawdown
- behavior: orders, fills, hold ratio, turnover events, memory-driven leverage
  amplification, and memory pollution ratios
- execution realism: fill rate, partial fill rate, rejected/pending orders, commission, slippage, latency
- risk awareness: lifecycle coverage, blocked/clipped decisions, violations, warning/error checks
- reproducibility: prompt/model/data/memory/tool/risk/portfolio/execution state coverage
- reasoning consistency: action side and target weight agreement

## Community Benchmark Submission Schema

External benchmark rows can be shared without exposing raw provider prompts or
responses. The minimal public submission contract lives at
[`../schemas/benchmark_submission.schema.json`](../schemas/benchmark_submission.schema.json).
It records the scenario, redacted agent metadata, data source, execution
configuration, risk configuration, metrics, trajectory manifest, redaction
policy, and reproducibility hash.

Validate an example submission with:

```bash
tradearena validate-submission examples/benchmark_submissions/example_redacted_submission.json
```

## Demo Artifact Contract

The demo artifact contract lives at
[`../schemas/demo_artifact_contract.schema.json`](../schemas/demo_artifact_contract.schema.json)
and is instantiated by [`demo_artifacts.yaml`](demo_artifacts.yaml). It lists
the commands and output files that should remain stable for quickstart,
execution-realism, audit-report, benchmark-card, and community-registry demos.

Validate it after building the showcase:

```bash
python scripts/validate_demo_artifacts.py
```

When a demo summary exposes `verification_commands`, the validator also checks
that the summary commands exactly match the manifest's `required_validators` so
artifact-local replay instructions cannot drift from the release contract.

## Broker Handoff, Approval, And Response Artifact Schemas

Broker handoff request artifacts can be validated against
[`../schemas/broker_handoff_artifact.schema.json`](../schemas/broker_handoff_artifact.schema.json).
The schema fixes the public `tradearena_broker_handoff_artifact_v0.1`
contract for adapter mode, account mode, safety flags, and broker-review order
rows.

Validate a broker handoff artifact with:

```bash
tradearena validate-broker-handoff outputs/examples/alpaca_paper_export/alpaca_paper_orders.json
```

Compute the canonical hash to place in a reviewed approval artifact with:

```bash
tradearena hash-broker-handoff path/to/broker_handoff.json
```

Broker approval artifacts can be validated against
[`../schemas/broker_approval_artifact.schema.json`](../schemas/broker_approval_artifact.schema.json).
The schema fixes the public `tradearena_broker_approval_artifact_v0.1`
contract for redacted operator approval, account mode, max notional, max
quantity, allowed symbols, allowed order types, and optional request-artifact
hashes. Approval timestamps must be ISO timestamps with timezone information;
runtime validation also requires `expires_at` to be later than `approved_at`
when an expiry is present.
Runtime code can consume this contract with
`broker_safety_from_approval_artifact(...)` to build a live human-approved
`BrokerSafetyConfig`; pass `now=` to reject expired approval artifacts during
validation or conversion. Use `broker_handoff_artifact_hash(...)` to populate
`request_artifact_hash` with a `sha256:` plus 64 lowercase hex value, and pass
`request_artifact=` to
`broker_safety_from_approval_artifact(...)` so live safety creation is bound to
the exact reviewed broker handoff artifact.

Validate a broker approval artifact with:

```bash
tradearena validate-broker-approval path/to/broker_approval.json --now 2026-05-31T12:30:00Z
```

Validate that the approval authorizes the exact reviewed handoff request with:

```bash
tradearena validate-broker-approval-binding path/to/broker_approval.json path/to/broker_handoff.json --now 2026-05-31T12:30:00Z
```

This binding check also verifies that request orders stay within the approval's
symbol, order-type, quantity, and notional limits. Each bound request order
must include a positive `limit_price` so notional can be checked before live
safety creation.

Broker response artifacts can be validated against
[`../schemas/broker_response_artifact.schema.json`](../schemas/broker_response_artifact.schema.json).
The schema fixes the public `tradearena_broker_response_artifact_v0.1`
contract for adapter mode, account mode, normalized broker statuses,
reconciliation counts, and redacted response rows.

Validate a broker response artifact with:

```bash
tradearena validate-broker-response outputs/examples/broker_response_reconciliation/broker_response_artifact.json
```

## Reproduction Report Schema

The external reproduction report schema lives at
[`../schemas/reproduction_report.schema.json`](../schemas/reproduction_report.schema.json).
It records commit/tag, Python environment, commands, output hashes, trajectory
hash, and whether live APIs, downloaded market data, or private fills were used.
Generate a no-key report with:

```bash
python scripts/run_external_reproduction_pack.py
```
