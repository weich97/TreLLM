# Discussion Seeds

Use these after enabling GitHub Discussions.

## General: What Should A Reproducible Trading-Agent Trajectory Include?

Prompt:

```text
TradeArena currently records observation, signals, proposed decisions, approved
decisions, risk reports, orders, fills, portfolio state, memory events,
execution simulator state, and random seed.

What fields would you add before trusting an LLM trading-agent benchmark?
```

## Ideas: Execution Realism Presets

Prompt:

```text
Which execution assumptions matter most for LLM trading-agent evaluation:
slippage, latency, order participation, partial fills, rejected orders, market
impact, spread, or something else?
```

## Q&A: Redacted Benchmark Submissions

Prompt:

```text
We want community benchmark submissions without exposing raw provider prompts or
responses. What should a redacted manifest include to be useful but safe?
```

## Ideas: Planning vs Live Trading Boundary

Prompt:

```text
The retail planning sandbox is paper-only and requires human approval. What is
the safest extension path for planning, paper trading, and broker adapters?
```
