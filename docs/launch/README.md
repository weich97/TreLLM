# TradeArena Project Metadata

Use this page for repository setup, project listings, and quickstart links.
TradeArena's public positioning is:

> We audit how autonomous financial agents move from intent to risk-aware,
> execution-realistic actions.

## Repository Positioning

Use this one-liner in GitHub, package metadata, and project listings:

```text
Open-source research prototype for financial-agent reliability, risk-aware AI systems, and intent-to-execution audit.
```

Longer description:

```text
TradeArena turns every financial-agent decision into a traceable trajectory:
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

- Publish GitHub release `v0.2.0`.
- Prepare patch release candidate `v0.2.1` from
  [`release_candidate_v0.2.1.md`](release_candidate_v0.2.1.md) after CI passes.
- Add the topics above.
- Enable GitHub Discussions.
- Verify the GitHub Pages site at `https://weich97.github.io/TradeArena/`.
- Create the issue backlog in `docs/launch/issue_backlog.md`.
- Verify the browser-playable 3-minute demo and link it from the README.
- Verify the v0.2 external reproduction pack with at least three independent
  reports: macOS/Python 3.10, Linux/Python 3.11, and Colab or Binder.
- Attach the execution calibration stability report, market-rule fixture report,
  and external validation bundle to the patch release notes.

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
Auditable financial-agent reliability framework with replayable trajectories, risk gates, paper execution, and quickstart demos.
```
