# Starter Issue Backlog

Use these as the first public issues so contributors immediately see where to
enter the project.

## Good First Issues

### Add a small Alpaca paper-trading adapter

Labels: `good first issue`, `adapter`, `paper-trading`

Build a paper-only broker adapter that converts approved TradeArena orders into
a neutral export format compatible with Alpaca paper-trading review. The first
version should not submit live orders.

Acceptance criteria:

- add a small adapter under `src/tradearena/tools/` or `planning/`
- write output under `outputs/examples/`
- add one smoke test
- document the human-approval boundary

### Add a holdings CSV importer for the retail planning sandbox

Labels: `good first issue`, `retail-planning`, `data`

Add a helper that loads holdings from a CSV with columns `symbol`, `market_value`,
`quantity`, and optional `cost_basis`, then feeds `examples/retail_planner_demo.py`.

### Add a new execution-stress preset

Labels: `good first issue`, `execution`, `benchmark`

Add one new preset to the execution realism sweep, such as low-volume
end-of-day conditions. The first high-spread preset landed in v0.1.1.

### Improve the visual tour accessibility text

Labels: `good first issue`, `docs`, `accessibility`

Review README GIF alt text, showcase copy, and HTML report headings for screen
reader clarity.

## Research Extensions

### Add a Deep RL policy baseline wrapper

Labels: `research extension`, `baseline`, `reinforcement-learning`

Add an interface example showing how a trained RL allocation policy can be
wrapped as a TradeArena strategy or analyst. The goal is integration and audit
compatibility, not state-of-the-art RL performance.

### Add a multi-window intraday benchmark registry

Labels: `research extension`, `benchmark`, `intraday`

Extend the 51-stock intraday probe to support temporally detached windows and
redacted manifest submission for community comparisons.

## Benchmark Requests

### Add a crypto market microstructure demo

Labels: `benchmark request`, `crypto`, `execution`

Create an offline-friendly crypto-style synthetic scenario with high volatility,
continuous trading, and liquidity-sensitive fills.

### Add a futures roll and expiry risk demo

Labels: `benchmark request`, `futures`, `risk`

Extend the retail planning or execution layer with futures expiry, roll windows,
and margin-call stress reporting.

## Discussion Seeds

These can become GitHub Discussions after Discussions are enabled:

- What should count as a reproducible LLM trading-agent trajectory?
- Which execution realism assumptions matter most for LLM agents?
- How should community benchmark submissions redact provider prompts/responses?
- What is the safest boundary between planning, paper trading, and live trading?
