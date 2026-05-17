# TradeArena Launch Kit

TradeArena should be launched as an audit and benchmark framework, not as an
"LLM trading bot." The core message:

> We make every LLM trading-agent decision reproducible, auditable, risk-gated,
> execution-realistic, and stress-testable.

## Repository Positioning

Use this one-liner in GitHub, social posts, and project listings:

```text
Open-source benchmark and audit framework for evaluating LLM trading agents under realistic execution, risk, and replayability constraints.
```

Longer description:

```text
TradeArena turns every trading decision into a traceable trajectory:
observation -> signal -> intended allocation -> risk gate -> order ->
fill/rejection -> portfolio state -> diagnostic report. It ships API-free demos
for audit reports, execution realism, risk gates, extension paths, A-share
rules, retail planning, and reproducible benchmark artifacts.
```

## GitHub Topics

Recommended topics:

```text
llm-agents
trading-agents
financial-ai
quantitative-finance
agent-benchmark
agent-evaluation
risk-management
execution-simulation
backtesting
portfolio-optimization
auditability
reproducible-research
python
benchmark
ai-agents
```

## Launch Checklist

- Publish GitHub release `v0.1.0`.
- Add the topics above.
- Enable GitHub Discussions.
- Create the issue backlog in `docs/launch/issue_backlog.md`.
- Pin the `v0.1.0` release and README demo GIFs in external posts.
- Share one command first: `python scripts/run_showcase.py`.

## Core Demo Command

```bash
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
```

Open:

```text
outputs/examples/showcase.html
```

## Suggested Repository Description

```text
Auditable, execution-realistic benchmark framework for LLM trading agents with replayable trajectories, risk gates, paper planning, and API-free demos.
```

## Suggested Social Tagline

```text
Do not just ask whether an LLM trading agent made money. Ask whether every
decision can be replayed, audited, risk-gated, and stress-tested.
```
