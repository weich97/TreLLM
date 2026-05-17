# TradeArena Project Metadata

Use this page for repository setup, project listings, and quickstart links.
TradeArena's public positioning is:

> We make every LLM trading-agent decision reproducible, auditable, risk-gated,
> execution-realistic, and stress-testable.

## Repository Positioning

Use this one-liner in GitHub, package metadata, and project listings:

```text
Open-source benchmark and audit framework for evaluating LLM trading agents under realistic execution, risk, and replayability constraints.
```

Longer description:

```text
TradeArena turns every trading decision into a traceable trajectory:
observation -> signal -> intended allocation -> risk gate -> order ->
fill/rejection -> portfolio state -> diagnostic report. It ships quickstart demos
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

## Repository Checklist

- Publish GitHub release `v0.1.0`.
- Add the topics above.
- Enable GitHub Discussions.
- Verify the GitHub Pages site at `https://weich97.github.io/TradeArena/`.
- Create the issue backlog in `docs/launch/issue_backlog.md`.
- Verify the browser-playable 3-minute demo and link it from the README.

## Core Demo Command

```bash
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
```

Open:

```text
outputs/examples/index.html
```

Watch in the browser:

```text
https://weich97.github.io/TradeArena/demo_video.html
```

## Suggested Repository Description

```text
Auditable, execution-realistic benchmark framework for LLM trading agents with replayable trajectories, risk gates, paper planning, and quickstart demos.
```
