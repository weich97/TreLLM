# Getting Started

TradeArena is easiest to evaluate as a sequence of small, offline-friendly artifacts.
The first run should show a working benchmark, an auditable trajectory, and a
visual demo portal before asking you to configure any model or data provider.

## Five-Minute Path

```bash
git clone https://github.com/weich97/TradeArena.git
cd TradeArena
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
```

Open:

```text
outputs/examples/index.html
```

The first-run path does not call DeepSeek, Poe, OpenAI, Hugging Face, AkShare,
or Yahoo Finance. It uses tracked data, deterministic synthetic markets, and
redacted metadata artifacts.

No local install yet? Use:

- [GitHub Codespaces][codespaces-quickstart]
- Colab notebook: [`notebooks/tradearena_5min_colab.ipynb`](../notebooks/tradearena_5min_colab.ipynb)

## Fifteen-Minute Path

```bash
python examples/audit_trajectory_walkthrough.py
python scripts/render_audit_report.py
python examples/execution_realism_sweep_demo.py
python examples/portfolio_markowitz_demo.py
python examples/visual_tour_demo.py
python examples/custom_plugin_demo.py
python examples/extension_walkthrough_demo.py
python examples/retail_planner_demo.py
```

Useful files:

- `outputs/examples/audit_report.html`
- `outputs/examples/benchmark-v0.1.html`
- `outputs/examples/showcase.html`
- `outputs/examples/execution_realism_sweep.svg`
- `outputs/examples/portfolio_markowitz.svg`
- `outputs/examples/visual_tour_index.html`
- `outputs/examples/custom_plugin.svg`
- `outputs/examples/extension_walkthrough.svg`
- `outputs/examples/retail_planning_report.html`
- `outputs/examples/audit_walkthrough_trajectory.json`

The execution realism sweep includes a `high_spread` preset. It keeps the same
agent and synthetic market but adds a quoted bid-ask spread so users can see
how crossing cost changes realized return and slippage even when fill rates do
not collapse.

## Extension Path

Start from `examples/custom_plugin_demo.py`. It defines one local analyst class
and reuses the existing runner, risk manager, execution simulator, memory store,
and evaluators.

Then run `examples/extension_walkthrough_demo.py`. It shows the fuller
contributor path: a custom analyst, a custom risk manager, and a custom
evaluator plugged into the same runner while the data provider, strategy,
execution simulator, memory store, and trajectory logger remain unchanged.

For an investor-facing extension, run `examples/retail_planner_demo.py`. It
uses a separate planning layer with investor profiles, goals, suitability
checks, paper rebalance instructions, and futures margin estimates.

## Quality Check

```bash
python -m pytest tests -q
python scripts/run_showcase.py --reuse-existing
python scripts/check_release_readiness.py
```

[codespaces-quickstart]: https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=weich97/TradeArena
