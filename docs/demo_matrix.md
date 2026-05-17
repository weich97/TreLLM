# Demo Matrix

This matrix maps TradeArena capabilities to hands-on repository artifacts. The
goal is to help a new user find one runnable example for each framework surface
without reading the full source tree.

## First-Run Surfaces

### Project Landing Page

- Run: `python scripts/run_showcase.py`
- Artifact: `outputs/examples/index.html`
- Shows: the static GitHub Pages landing page and core entry points.

### Quickstart Repo Tour

- Run: `python scripts/run_showcase.py`
- Artifact: `outputs/examples/showcase.html`
- Shows: a public-facing demo surface with links to every generated artifact.

### Benchmark v0.1 Card

- Run: `python scripts/build_benchmark_page.py`
- Artifacts:
  - `outputs/examples/benchmark-v0.1.html`
  - `docs/results/benchmark_v0_1.md`
- Shows: crisis scenes, intraday portfolio probes, execution-aware baselines,
  and representation robustness as a compact result page.

## Audit And Execution

### Auditable Trajectories

- Run:
  - `python examples/audit_trajectory_walkthrough.py`
  - `python scripts/render_audit_report.py`
- Artifact: `outputs/examples/audit_report.html`
- Shows: a decision traced from observation to risk gate, fills, memory, and
  reproducibility metadata.

### Execution Realism

- Run: `python examples/execution_realism_sweep_demo.py`
- Artifact: `outputs/examples/execution_realism_sweep.svg`
- Shows: the same agent under slippage, latency, liquidity limits, and
  rejections.

### Risk Lifecycle

- Run: `python examples/ashare_market_rules_demo.py`
- Artifact: `outputs/examples/ashare_market_rules.svg`
- Shows: hard A-share market rules as clipped or blocked risk reports.

## Data And Portfolio Baselines

### Data Extensibility

- Run: `python examples/sidecar_data_demo.py`
- Artifact: `outputs/examples/sidecar_data/`
- Shows: optional news, macro, filings, and alt-data sidecars entering the
  observation schema.

### A-Share Data Bridge

- Run: `python examples/akshare_csv_reuse_demo.py`
- Artifact: `outputs/examples/akshare_csv_reuse.svg`
- Shows: AkShare-style data normalized once and reused by the standard CSV
  provider.

### Portfolio Baselines

- Run: `python examples/portfolio_markowitz_demo.py`
- Artifact: `outputs/examples/portfolio_markowitz.svg`
- Shows: buy-and-hold, signal-weighted, and MVO strategies in the same
  evaluation stack.

## LLM And Diagnostics

### LLM Manifest Portability

- Run: `python examples/llm_cache_replay_demo.py`
- Artifact: `outputs/examples/llm_cache_replay_summary.json`
- Shows: redacted provider/model coverage, prompt mode counts, parse coverage,
  and replay fingerprints without raw provider text.

### Animated Visual Tour

- Run: `python examples/visual_tour_demo.py`
- Artifact: `outputs/examples/visual_tour_index.html`
- Shows: README-style lifecycle, execution, and diagnostics animations as
  reproducible local artifacts.

## Extensibility

### Plugin Extensibility

- Run: `python examples/custom_plugin_demo.py`
- Artifact: `outputs/examples/custom_plugin.svg`
- Shows: a new analyst swapped in without editing the runner, risk, execution,
  memory, or evaluators.

### Contributor Extension Path

- Run: `python examples/extension_walkthrough_demo.py`
- Artifact: `outputs/examples/extension_walkthrough.svg`
- Shows: a custom analyst, risk manager, and evaluator reusing the rest of the
  framework.

### Retail Planning Sandbox

- Run: `python examples/retail_planner_demo.py`
- Artifact: `outputs/examples/retail_planning_report.html`
- Shows: investor profiles, suitability gates, target allocations, futures
  margin estimates, and paper rebalance orders.
