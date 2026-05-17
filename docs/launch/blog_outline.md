# Blog Outline

Working title:

```text
From Leaderboard Returns To Auditable LLM Trading Decisions
```

## Hook

Many LLM trading demos show a final return curve. That is not enough. A trading
agent can look good in a simplified backtest while relying on unrealistic fills,
untracked prompts, hidden memory state, data leakage, or risk violations.

## Thesis

AI trading agents should be studied as auditable decision-making systems, not
only as predictors or strategy generators.

## Show The Decision Trace

Explain the TradeArena lifecycle:

```text
observation -> signal -> intended allocation -> risk gate -> order ->
fill/rejection -> portfolio state -> diagnostic report
```

Use `docs/assets/readme_audit_lifecycle.gif`.

## Why Execution Realism Changes Evaluation

Show how fees, slippage, latency, liquidity constraints, partial fills, and
rejections change measured behavior. Use the execution realism GIF and
`outputs/examples/execution_realism_sweep.svg`.

## Risk Is A Lifecycle, Not A Post-Hoc Metric

Describe pre-trade gates, in-trade monitors, post-trade attribution, and
structured risk reports. Mention A-share T+1 and price-limit demos as examples
of hard rule interventions.

## Reproducibility Without API Keys

Explain the first-run path:

```bash
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
```

No model keys or live data downloads are required.

## What Contributors Can Add

Point to:

- custom analyst/risk/evaluator walkthrough
- retail planning sandbox
- execution stress presets
- community benchmark registry

## Close

Do not just ask whether an LLM trading agent made money. Ask whether every
decision can be replayed, audited, risk-gated, and stress-tested.
