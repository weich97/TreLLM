# Getting Started

TradeArena is easiest to evaluate as a sequence of small, API-free artifacts.
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
outputs/examples/showcase.html
```

The first-run path does not call DeepSeek, Poe, OpenAI, Hugging Face, AkShare,
or Yahoo Finance. It uses tracked data, deterministic synthetic markets, and
redacted metadata artifacts.

## Fifteen-Minute Path

```bash
python examples/audit_trajectory_walkthrough.py
python scripts/render_audit_report.py
python examples/execution_realism_sweep_demo.py
python examples/portfolio_markowitz_demo.py
python examples/visual_tour_demo.py
python examples/custom_plugin_demo.py
python examples/extension_walkthrough_demo.py
```

Useful files:

- `outputs/examples/audit_report.html`
- `outputs/examples/execution_realism_sweep.svg`
- `outputs/examples/portfolio_markowitz.svg`
- `outputs/examples/visual_tour_index.html`
- `outputs/examples/custom_plugin.svg`
- `outputs/examples/extension_walkthrough.svg`
- `outputs/examples/audit_walkthrough_trajectory.json`

## Extension Path

Start from `examples/custom_plugin_demo.py`. It defines one local analyst class
and reuses the existing runner, risk manager, execution simulator, memory store,
and evaluators.

Then run `examples/extension_walkthrough_demo.py`. It shows the fuller
contributor path: a custom analyst, a custom risk manager, and a custom
evaluator plugged into the same runner while the data provider, strategy,
execution simulator, memory store, and trajectory logger remain unchanged.

## Quality Check

```bash
python -m pytest tests -q
python scripts/run_showcase.py --reuse-existing
```
