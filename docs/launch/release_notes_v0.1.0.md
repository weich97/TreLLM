# v0.1.0: Auditable Benchmark Release For LLM Trading Agents

TradeArena v0.1.0 is the first public benchmark release for evaluating LLM
trading agents as auditable decision-making systems under realistic market
constraints.

## Highlights

- **Quickstart showcase:** run `python scripts/run_showcase.py` to generate a
  local demo portal without model keys or live market-data downloads.
- **Captioned demo video:** watch or regenerate a 3-minute walkthrough of the
  showcase portal, audit report, execution realism, extension walkthrough, and
  retail planning sandbox.
- **Replayable audit trajectories:** every decision records observation,
  signals, intended allocation, risk-gate changes, orders, fills/rejections,
  portfolio state, memory, and reproducibility metadata.
- **Execution realism:** built-in simulator models fees, slippage, latency,
  liquidity constraints, partial fills, pending orders, and rejections.
- **Risk lifecycle:** pre-trade gates, in-trade monitors, post-trade
  attribution, suitability checks, and risk-violation logs are first-class
  artifacts.
- **Hands-on extensions:** examples cover custom analysts, custom risk modules,
  custom evaluators, A-share rules, AkShare CSV reuse, retail planning, and
  paper rebalance reports.
- **Research-grade diagnostics:** tracked artifacts show representation
  signatures, crisis-scene probes, feedback-alignment diagnostics, and 51-stock
  intraday portfolio behavior without exposing raw provider prompt/response
  caches.

## Quick Start

```bash
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
```

Open:

```text
outputs/examples/showcase.html
```

## What This Release Is Not

TradeArena is not a live trading bot and does not promise profitable trading.
It is a benchmark, simulation, and audit framework for studying whether LLM
trading agents can be reproduced, inspected, risk-gated, and evaluated under
realistic constraints.

## Suggested GitHub Release Title

```text
v0.1.0: Auditable benchmark release for LLM trading agents
```
