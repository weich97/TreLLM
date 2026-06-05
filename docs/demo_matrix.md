# Demo Matrix

This matrix maps TreLLM capabilities to hands-on repository artifacts. The
goal is to help a new user find one runnable example for each TreLLM system surface
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

### Benchmark v0.2 Card

- Run: `python scripts/build_benchmark_page.py`
- Artifacts:
  - `outputs/examples/benchmark-v0.2.html`
  - `docs/results/benchmark_v0_2.md`
- Shows: crisis scenes, intraday portfolio probes, execution-aware baselines,
  and representation robustness as a compact result page.

### Classical Baseline Matrix

- Run: `python scripts/run_classical_baseline_matrix.py`
- Artifacts:
  - `docs/results/classical_baselines/classical_baselines.md`
  - `docs/results/classical_baselines/classical_vs_llm_comparison.csv`
- Shows: buy-and-hold, equal weight, naive momentum, mean reversion, risk
  parity, minimum variance, Markowitz/MVO, random, and always-hold on the same
  synthetic and Yahoo Finance scenarios as the model leaderboard.

### Decision/Execution Quality Radar

- Run: `python scripts/build_quality_decomposition.py`
- Artifacts:
  - `docs/results/quality_decomposition/quality_decomposition.md`
  - `docs/results/quality_decomposition/decision_execution_radar.svg`
- Shows: alpha quality, risk discipline, and execution robustness as separate
  benchmark dimensions.

## Audit And Execution

### Auditable Trajectories

- Run:
  - `python examples/audit_trajectory_walkthrough.py`
  - `python scripts/render_audit_report.py`
- Artifact: `outputs/examples/audit_report.html`
- Shows: a decision traced from observation to risk gate, fills, memory, and
  reproducibility metadata.

### Agent Autopsy Dashboard

- Run:
  - `python examples/audit_trajectory_walkthrough.py`
  - `python scripts/render_agent_autopsy_dashboard.py`
  - `python scripts/run_failure_autopsy.py`
- Artifact: `outputs/examples/agent_autopsy_dashboard.html`
- Shows: intent versus executed weights, slippage attribution, a risk
  intervention timeline, and fixed failure-mode counts from the same replayable
  trajectory.

### Replay Mode

- Run: `tradearena replay outputs/examples/audit_walkthrough_trajectory.json --step 17`
- Artifact: terminal step summary, or JSON with `--json`
- Shows: one timestamp's observation, signals, proposed decisions, risk edits,
  execution state, portfolio, and reproducibility fingerprint.

### Execution Realism

- Run: `python examples/execution_realism_sweep_demo.py`
- Artifact: `outputs/examples/execution_realism_sweep.svg`
- Shows: the same agent under spread, slippage, latency, liquidity limits,
  and rejections.

### Crypto Microstructure Stress

- Run: `python examples/crypto_microstructure_stress_demo.py`
- Artifact: `outputs/examples/crypto_microstructure_stress/crypto_microstructure_stress.svg`
- Shows: a no-key synthetic crypto path with high volatility, low participation,
  latency, partial fills, rejections, and slippage metrics.

### Risk Lifecycle

- Run: `python examples/ashare_market_rules_demo.py`
- Artifact: `outputs/examples/ashare_market_rules.svg`
- Shows: hard A-share market rules as clipped or blocked risk reports.

### Futures Roll Risk

- Run: `python examples/futures_roll_risk_demo.py`
- Artifact: `outputs/examples/futures_roll_risk/futures_roll_risk.svg`
- Shows: contract metadata, a roll schedule, and expiry/roll-window warnings in
  a normal `RiskReport`.

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

### Mock Deep-RL Policy Baseline

- Run: `python examples/rl_policy_baseline_demo.py`
- Artifact: `outputs/examples/rl_policy_baseline/rl_policy_baseline.svg`
- Shows: a deterministic CI-safe policy wrapper that emits normal decisions and
  reuses risk, execution, trajectory, and evaluator plugins.

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
  TreLLM stack.

### Retail Planning Sandbox

- Run: `python examples/retail_planner_demo.py`
- Artifact: `outputs/examples/retail_planning_report.html`
- Shows: investor profiles, suitability gates, target allocations, futures
  margin estimates, and paper rebalance orders.

### Holdings CSV Import

- Run: `python examples/holdings_csv_import_demo.py`
- Artifact: `outputs/examples/holdings_csv_import/summary.json`
- Shows: a tiny holdings CSV fixture entering the retail planning sandbox.

### Paper Broker Export

- Run: `python examples/alpaca_paper_export_demo.py`
- Artifact: `outputs/examples/alpaca_paper_export/alpaca_paper_orders.json`
- Shows: approved orders converted into Alpaca-compatible paper-review rows
  without live submission.

### Dry-Run Broker Adapter

- Run: `python examples/dry_run_broker_adapter_demo.py`
- Artifact: `outputs/examples/dry_run_broker_adapter/dry_run_orders.json`
- Shows: request-shape validation through the generic broker adapter contract
  without broker credentials, network calls, or live submission.

### Broker Approval Safety

- Run: `python examples/broker_approval_safety_demo.py`
- Artifact: `outputs/examples/broker_approval_safety/broker_approval_artifact.json`
- Shows: a redacted approval artifact converted into a live-mode safety gate
  that allows bounded orders and blocks oversized ones without broker calls.

### Broker Response Reconciliation

- Run: `python examples/broker_response_reconciliation_demo.py`
- Artifact: `outputs/examples/broker_response_reconciliation/broker_response_artifact.json`
- Shows: paper broker responses matched back to submitted client order IDs,
  including filled, partially filled, rejected, missing, and unmatched rows.

### Live-Readiness Contract

- Read:
  - `docs/live_trading_readiness.md`
  - `docs/broker_adapter_contract.md`
- Artifact: staged checklist and broker adapter safety contract.
- Shows: how TreLLM should progress from paper research to broker-review
  exports, paper sandboxes, and future human-approved live adapters without
  making live submission a default path.
