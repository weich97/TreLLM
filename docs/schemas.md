# TradeArena Schemas

TradeArena treats an LLM trading agent as an auditable lifecycle, not a black-box signal generator. A benchmark step records the following protocol surfaces.

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

## Risk Schema

- `RiskBudget`: position weight, gross exposure, turnover, drawdown, participation, confidence, latency, slippage limits
- `RiskCheck`: named constraint check with pass/fail, severity, message
- `RiskViolation`: phase, constraint, observed value, limit, severity, symbol
- `RiskReport`: phase-level audit object for pre-trade, in-trade, and post-trade stages
- `RiskAttribution`: post-trade PnL/cost/exposure attribution

## Memory Schema

- append-only events
- trade journal entries
- thesis tracking
- failure cases
- digest for reproducibility checks

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
- behavior: orders, fills, hold ratio, turnover events
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
