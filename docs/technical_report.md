# TradeArena: Auditable And Execution-Realistic Evaluation For LLM Trading Agents

This technical note summarizes the public v0.1 framework and benchmark
artifacts. It is intentionally separate from any manuscript source: the goal is
to give repository users a citable engineering overview and reproduction path.

## Motivation

Returns-only evaluation is fragile for LLM trading agents. A result can change
with prompt version, model version, retrieved context, tool outputs, memory
state, risk constraints, portfolio state, execution simulator state, and random
seed. TradeArena records these surfaces as a replayable trajectory rather than
only reporting final equity.

## Framework

TradeArena treats each trading step as an auditable lifecycle:

```text
observation -> signal -> intended allocation -> risk gate -> order
  -> fill/rejection -> portfolio state -> memory -> diagnostic report
```

The framework exposes narrow interfaces for data providers, analysts,
strategies, risk managers, execution simulators, memory stores, and evaluators.
This lets contributors replace one module without rewriting the rest of the
benchmark runner.

## Benchmark Axes

- **Execution realism:** fees, slippage, latency, liquidity participation
  limits, partial fills, pending orders, and rejected orders.
- **Risk lifecycle:** pre-trade gates, in-trade monitors, post-trade
  attribution, clipped decisions, blocked decisions, and violation logs.
- **Reproducibility:** prompt/model metadata, market timestamps, memory digest,
  random seed, portfolio state, risk configuration, and execution state.
- **Behavioral diagnostics:** representation signatures, risk-feedback
  alignment, correlation blind spots, and audit completeness.

## Public v0.1 Artifacts

- [`docs/results/benchmark_v0_1.md`](results/benchmark_v0_1.md): compact
  benchmark snapshot.
- [`docs/results/crisis`](results/crisis): crisis-scene LLM rows and
  representation summaries.
- [`docs/results/intraday`](results/intraday): 51-stock intraday portfolio
  probe tables.
- [`docs/results/representation`](results/representation): rolling
  representation robustness tables.
- [`schemas/benchmark_submission.schema.json`](../schemas/benchmark_submission.schema.json):
  redacted community submission contract.

## Reproduction

```bash
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
python scripts/check_release_readiness.py
```

Open `outputs/examples/index.html` for the landing page or
`outputs/examples/benchmark-v0.1.html` for the benchmark snapshot.

## Scope

TradeArena is not financial advice and not a live trading system. Its claim is
methodological: auditable risk feedback and execution-aware trajectories reveal
when LLM financial-agent behavior is aligning, drifting, or failing.
