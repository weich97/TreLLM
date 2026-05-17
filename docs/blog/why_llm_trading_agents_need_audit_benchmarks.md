# Why LLM Trading Agents Need Audit Benchmarks, Not Just Return Curves

Most trading-agent demos answer one question: did the agent make money?

That is not enough for LLM agents. A model-backed trading decision depends on
prompt version, model version, retrieved context, tool outputs, memory state,
portfolio state, risk constraints, market timestamp, execution assumptions, and
random seed. If those surfaces are not recorded, a return curve is hard to
audit and harder to reproduce.

TradeArena takes a different view. It treats an LLM trading agent as an
auditable decision-making system:

```text
observation -> signal -> intended allocation -> risk gate -> order
  -> fill/rejection -> portfolio state -> diagnostic report
```

## What Changes Under Realistic Execution?

Ideal backtests often assume immediate fills. TradeArena exposes the friction:

- fees and slippage
- latency
- liquidity participation limits
- partial fills
- pending and rejected orders

The v0.1 benchmark card shows why this matters. Under realistic execution,
evaluation includes fill rate, rejection rate, risk edits, and audit
completeness alongside return and drawdown.

## Why Risk Gates Matter

LLM agents can produce confident allocations that violate risk budgets or
market rules. TradeArena makes the intervention explicit:

- intended decisions
- approved decisions
- clipped or blocked decisions
- pre-trade risk reports
- in-trade monitor reports
- post-trade attribution

Risk gates are not cosmetic. They are part of the benchmark outcome.

## Why Audit Reports Matter

A useful benchmark should answer:

- What did the agent see?
- What did it propose?
- Which risk checks changed the action?
- Which orders filled, partially filled, or failed?
- What portfolio state resulted?
- Which reproducibility fields identify the run?

TradeArena renders this as a browser-readable audit report and keeps compact
result snapshots for public reproduction.

## Try It

```bash
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
```

Then open:

- `outputs/examples/index.html`
- `outputs/examples/benchmark-v0.1.html`
- `outputs/examples/audit_report.html`

GitHub Pages:

- <https://weich97.github.io/TradeArena/>
- <https://weich97.github.io/TradeArena/benchmark-v0.1.html>

TradeArena is not financial advice and not a live trading bot. It is an
open-source benchmark and audit framework for studying whether LLM trading
agents are reproducible, risk-aware, and execution-realistic.
