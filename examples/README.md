# TradeArena Hands-On Examples

These examples are designed for the first hour after cloning. They avoid live
LLM calls by default and write local artifacts under `outputs/examples/`.

## Recommended First Run

```bash
python scripts/run_showcase.py
```

Open:

```text
outputs/examples/showcase.html
```

The showcase links to a practical tour of auditable trajectories, execution
realism, animated visual diagnostics, A-share market-rule interventions,
portfolio baselines, redacted LLM cache manifests, and a custom plugin
extension plus a contributor extension walkthrough.

## 1. Core Benchmark

```bash
python examples/quickstart_core_benchmark.py
```

Shows how two benchmark cases share the same market, risk, execution, and
evaluation stack.

Output:

- `outputs/examples/quickstart_core_metrics.json`

## 2. Animated Visual Tour

```bash
python examples/visual_tour_demo.py
```

Regenerates the README-style audit lifecycle, execution realism, and
diagnostics animations as local hands-on artifacts.

Output:

- `outputs/examples/visual_tour_index.html`
- `outputs/examples/visual_tour_summary.json`
- `outputs/examples/visual_tour_audit_lifecycle.gif`
- `outputs/examples/visual_tour_execution_realism.gif`
- `outputs/examples/visual_tour_diagnostics_loop.gif`

## 3. Audit Trajectory Walkthrough

```bash
python examples/audit_trajectory_walkthrough.py
python scripts/render_audit_report.py
```

Shows one complete observe-plan-risk-act-reflect trajectory, including risk
clipping, pending orders, rejected orders, fills, memory events, and
reproducibility metadata.

Output:

- `outputs/examples/audit_walkthrough_trajectory.json`
- `outputs/examples/audit_report.html`

## 4. Optional Data Sidecars

```bash
python examples/sidecar_data_demo.py
```

Shows how `news.csv`, `macro.csv`, `filings.csv`, and
`alternative_data.csv` can enter observations through the CSV provider without
changing the runner.

Output:

- `outputs/examples/sidecar_data/`

## 5. AkShare CSV Reuse

```bash
python examples/akshare_csv_reuse_demo.py
```

Shows the recommended A-share integration boundary: download data once,
normalize to OHLCV CSV, and reuse the standard `CsvMarketDataProvider`.

Output:

- `outputs/examples/akshare_csv_reuse_summary.json`
- `outputs/examples/akshare_csv_reuse.svg`

Live download command:

```bash
python -m pip install -e ".[ashare]"
python scripts/download_akshare_ashare_daily.py --symbols 600519.SS,300750.SZ --start 2021-01-01 --end 2026-05-14 --output-dir data/real/akshare_ashare_daily
```

## 6. A-Share Market Rules

```bash
python examples/ashare_market_rules_demo.py
```

Shows how T+1, 10% price limits, and 100-share board lots become auditable
risk-gate outcomes.

Output:

- `outputs/examples/ashare_market_rules_summary.json`
- `outputs/examples/ashare_market_rules_orders.csv`
- `outputs/examples/ashare_market_rules.svg`

## 7. Execution Realism Sweep

```bash
python examples/execution_realism_sweep_demo.py
```

Shows how fees, slippage, latency, liquidity limits, and rejections change
agent behavior.

Output:

- `outputs/examples/execution_realism_sweep_summary.json`
- `outputs/examples/execution_realism_sweep.csv`
- `outputs/examples/execution_realism_sweep.svg`

## 8. Portfolio / Markowitz Baselines

```bash
python examples/portfolio_markowitz_demo.py
```

Shows passive, signal-weighted, and MVO-style allocation through the same
strategy and evaluator interfaces.

Output:

- `outputs/examples/portfolio_markowitz_summary.json`
- `outputs/examples/portfolio_markowitz.csv`
- `outputs/examples/portfolio_markowitz.svg`

## 9. Representation Diagnostics

```bash
python examples/representation_signature_demo.py
```

Shows how tracked diagnostic tables can be turned into an API-free visual
artifact.

Output:

- `outputs/examples/representation_signature_summary.json`
- `outputs/examples/representation_signature.svg`

## 10. Custom Plugin Extension

```bash
python examples/custom_plugin_demo.py
```

Shows a local analyst plugin running through the existing strategy, risk,
execution, memory, and evaluator stack.

Output:

- `outputs/examples/custom_plugin_summary.json`
- `outputs/examples/custom_plugin.svg`

## 11. Contributor Extension Walkthrough

```bash
python examples/extension_walkthrough_demo.py
```

Shows how to add a custom analyst, risk manager, and evaluator without editing
the core runner.

Output:

- `outputs/examples/extension_walkthrough_summary.json`
- `outputs/examples/extension_walkthrough.svg`
- `outputs/examples/extension_walkthrough_notes.md`

## 12. Redacted LLM Cache Manifest

```bash
python examples/llm_cache_replay_demo.py
```

Shows portable model-experiment metadata without shipping raw prompt/response
text.

Output:

- `outputs/examples/llm_cache_replay_summary.json`

## Full Local Check

```bash
python -m pytest tests -q
python scripts/run_showcase.py --reuse-existing
```
