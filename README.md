<p align="center">
  <img src="docs/assets/tradearena_wordmark.svg"
       alt="TradeArena wordmark"
       width="780">
</p>

<p align="center">
  <strong>
    Research code for testing LLM trading agents with paper execution,
    risk checks, and reproducible logs.
  </strong>
</p>

<p align="center">
  <a href="https://github.com/weich97/TradeArena/actions/workflows/ci.yml">
    <img alt="CI status" src="https://github.com/weich97/TradeArena/actions/workflows/ci.yml/badge.svg">
  </a>
  <a href="https://pypi.org/project/tradearena-benchmark/">
    <img alt="PyPI version" src="https://img.shields.io/pypi/v/tradearena-benchmark">
  </a>
  <a href="https://pypi.org/project/tradearena-benchmark/">
    <img alt="Python versions" src="https://img.shields.io/pypi/pyversions/tradearena-benchmark">
  </a>
  <a href="https://github.com/weich97/TradeArena/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/weich97/TradeArena">
  </a>
  <a href="https://codecov.io/gh/weich97/TradeArena">
    <img alt="Coverage" src="https://codecov.io/gh/weich97/TradeArena/branch/main/graph/badge.svg">
  </a>
</p>

<p align="center">
  <a href="docs/getting_started.md">Getting started</a> |
  <a href="https://pypi.org/project/tradearena-benchmark/">PyPI</a> |
  <a href="https://weich97.github.io/TradeArena/">Project site</a> |
  <a href="https://weich97.github.io/TradeArena/agent_autopsy_dashboard.html">Agent Autopsy</a> |
  <a href="https://weich97.github.io/TradeArena/benchmark-v0.1.html">Benchmark card</a> |
  <a href="https://weich97.github.io/TradeArena/community_registry.html">Leaderboard</a> |
  <a href="docs/benchmark_submissions.md">Redacted manifests</a> |
  <a href="docs/plugin_development.md">Plugins</a> |
  <a href="docs/benchmark_maturity.md">Maturity track</a> |
  <a href="docs/community_tasks.md">First issues</a> |
  <a href="docs/contributor_roadmap.md">Roadmap</a> |
  <a href="SECURITY.md">Security</a>
</p>

<p align="center">
  <a href="https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=weich97/TradeArena">
    <img alt="Open in GitHub Codespaces"
         src="https://img.shields.io/badge/Open%20in-Codespaces-181717?logo=github">
  </a>
  <a href="https://colab.research.google.com/github/weich97/TradeArena/blob/main/notebooks/tradearena_5min_colab.ipynb">
    <img alt="Open in Colab"
         src="https://colab.research.google.com/assets/colab-badge.svg">
  </a>
  <a href="https://mybinder.org/v2/gh/weich97/TradeArena/main?filepath=notebooks%2Ftradearena_5min_colab.ipynb">
    <img alt="Launch Binder"
         src="https://mybinder.org/badge_logo.svg">
  </a>
  <a href="https://nbviewer.org/github/weich97/TradeArena/blob/main/notebooks/tradearena_5min_colab.ipynb">
    <img alt="View notebook"
         src="https://img.shields.io/badge/View-nbviewer-f37626">
  </a>
</p>

# TradeArena

TradeArena runs paper-trading experiments for LLM and deterministic agents. For
each step it records the market input, proposed weights, risk edits, simulated
fills, portfolio state, and metrics.

<p align="center">
  <img src="docs/assets/readme_audit_lifecycle.gif"
       alt="Animated TradeArena audit trace showing observation, plan, risk review, execution, and reflection records."
       width="920">
</p>

<p align="center">
  <img src="docs/assets/readme_pipeline_architecture.svg"
       alt="TradeArena runtime architecture: market inputs feed an agent observe-plan loop, a risk gate, an execution simulator, portfolio state, memory feedback, and replayable audit artifacts."
       width="980">
</p>

TradeArena only runs paper experiments. The default examples never submit live
orders. The benchmark is still early; the repo is most useful for checking how
agent intent changes after risk checks and paper-execution costs.

## Why TradeArena?

TradeArena is not a replacement for mature backtesting engines. It is a small
audit harness for asking what happened between an agent's stated intent and the
paper order that survived risk and execution stress.

| Tool | Best fit | TradeArena relationship |
| --- | --- | --- |
| Backtrader | Event-driven strategy backtests and broker-style order workflows | Use when the main object is a classical strategy backtest; TradeArena focuses on agent traces, risk edits, and redacted LLM manifests. |
| vectorbt | Fast vectorized research over many parameter settings | Use when large array sweeps matter most; TradeArena trades speed for step-level audit records and execution/risk reports. |
| FinRL | Reinforcement-learning market environments and policy training | Use for RL policy development; TradeArena can wrap learned or deterministic policies as agents and compare their risk/execution behavior. |
| TradeArena | Paper-only LLM/deterministic agent evaluation with reproducible trajectories | Use when prompts, decisions, risk gates, fills, memory, and benchmark manifests need to be inspected together. |

## How A Run Works

The runner in
[`src/tradearena/core/runner.py`](src/tradearena/core/runner.py) executes the
same loop at every market timestamp: read the market snapshot, collect analyst
signals, build target weights, apply the risk gate, simulate fills, update the
portfolio, and write the logs.

The default allocation logic is intentionally simple and inspectable. In
[`SignalWeightedStrategy`](src/tradearena/agents/strategy.py), analyst signals
are grouped by symbol, confidence-weighted, and converted into target weights:

```text
combined_score(symbol) =
  sum(signal.score * max(0.01, signal.confidence)) /
  sum(max(0.01, signal.confidence))

target_weight = clip(5 * combined_score, -max_short_weight, max_long_weight)
```

Small scores inside the deadband become `HOLD`. The optional
[`MemoryAwareSignalWeightedStrategy`](src/tradearena/agents/strategy.py) applies
a decayed memory overlay when recent memory contains drawdowns, rejected orders,
or risk violations. It records the configured `memory_decay_rate`, a weighted
`memory_pollution_ratio` for noisy or invalid memory events, and
`memory_driven_leverage_amplification`, the per-decision ratio between
memory-adjusted and base target exposure. Classical baselines are also available, including equal
buy-and-hold and a rolling minimum-variance strategy that estimates realized
covariance from the current trajectory only.

Execution is split into two stages. First,
[`TargetWeightExecutionAgent`](src/tradearena/agents/execution.py) translates
approved target weights into market orders by comparing current position value
with target portfolio value. Trades below `min_trade_value` are skipped to avoid
noise. Second,
[`RealisticOrderSimulator`](src/tradearena/tools/simulator.py) applies a
configurable paper-execution stress model:

- submitted orders enter a pending queue and become eligible after
  `latency_steps`;
- per-symbol fill capacity is capped by `bar.volume * participation_rate`;
- buys cannot exceed available cash, and sells cannot exceed holdings unless
  shorting is enabled;
- market orders cross half the configured bid-ask spread;
- execution price includes base slippage, spread, market impact, and intrabar
  volatility:

```text
slip_rate =
  spread_bps / 20000
  + base_slippage_bps / 10000
  + market_impact * (filled_quantity / volume)
  + 0.1 * ((high - low) / close)
```

The simulator writes an `ExecutionReport` with quantities, fill ratio, latency,
available liquidity, fees, slippage cost, partial fills, pending orders, and
rejections. The defaults are stress-test settings. They are not broker-grade
transaction-cost calibration.

## Execution Assumptions

The simulator is deliberately simple. The important parameters are:

| Parameter | Default role | Calibration source needed |
| --- | --- | --- |
| `commission_bps` | explicit fee on traded notional | broker or exchange fee schedule |
| `spread_bps` | full quoted spread; market orders cross half | quote/NBBO or order-book snapshots |
| `base_slippage_bps` | residual shortfall before spread, impact, and bar volatility | historical order/fill logs |
| `participation_rate` | cap on fillable bar volume | execution policy or parent-order participation target |
| `latency_steps` | bar-delay before an order is eligible | submission, acknowledgement, and fill timestamps |
| `market_impact` | coefficient on participation | regression of implementation shortfall on participation |

The tracked Yahoo Finance OHLCV files are enough for bar ranges, rough volume
checks, and participation caps. They are not enough for quoted spread, queue
depth, fee tier, latency, or realized shortfall. Treat the included benchmark
numbers as stress comparisons under shared assumptions. For execution claims,
replace the defaults with parameters fitted from quotes and fills.

Run the diagnostic:

```bash
python scripts/calibrate_execution_model.py --data-dir data/real/yahoo_intraday_1h_50
```

This writes `docs/results/execution_calibration_intraday_1h.json` and
`docs/results/execution_calibration_intraday_1h.md`. Full details are in
[`docs/execution_model.md`](docs/execution_model.md), including the
`scripts/compare_execution_to_fills.py` workflow for comparing private or
licensed historical fills against the simulator equation.

Risk control runs before, during, and after simulated execution.
[`MaxPositionRiskManager`](src/tradearena/agents/risk.py) runs three checks:

- pre-trade approval clips per-symbol weights to `max_abs_weight`, blocks
  decisions below `min_confidence`, rescales gross exposure above
  `max_gross_exposure`, forces de-risking when the rolling drawdown kill switch
  breaches `max_drawdown`, and reports projected turnover above
  `max_single_step_turnover`;
- in-trade monitoring checks realized participation, latency, and slippage
  against `max_order_participation`, `max_latency_steps`, and
  `max_slippage_bps`;
- post-trade attribution reports realized PnL, commission, slippage cost, and
  final exposures.

Each intervention is saved as a `RiskReport` with `RiskCheck` and
`RiskViolation` records. That makes it possible to compare the model's original
intent with the order that actually reached the simulator.

## Quick Start: Deterministic Smoke Test

```bash
python -m pip install tradearena-benchmark
tradearena --benchmark tradearena-core
```

This command does **not** call an LLM. It is a no-key smoke test for the runner,
log schema, risk gate, execution simulator, and metrics. It uses deterministic
analysts so a fresh checkout can be tested before API keys or billing are
involved.

The PyPI distribution is `tradearena-benchmark` because `tradearena` is already
occupied on PyPI by an unrelated project. The import namespace and CLI remain
`tradearena`.

## 5 Minutes To A Result

One command writes a replayable trajectory JSON:

```bash
tradearena --benchmark tradearena-core --periods 30 --output outputs/examples/quickstart_trajectory.json
```

Then verify the run identity:

```bash
tradearena hash-run outputs/examples/quickstart_trajectory.json
```

Replay one trajectory step in the terminal:

```bash
tradearena replay outputs/examples/quickstart_trajectory.json --case risk_aware_realistic_agent --step 17
```

The first artifact to inspect is
`outputs/examples/quickstart_trajectory.json`: it contains the decisions,
pre-trade risk reports, simulated fills, portfolio states, and metrics for each
case. For browser reports, run the local showcase below.

To run the local demo portal:

```bash
git clone https://github.com/weich97/TradeArena.git
cd TradeArena
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
```

Then open:

```text
outputs/examples/index.html
outputs/examples/agent_autopsy_dashboard.html
```

If you are deciding whether the project is worth using, start with this command
and inspect the generated reports before setting up model keys, market-data
downloads, or broker-facing code.

The first-run path uses deterministic agents, tracked snapshots, and local demo
files. It does not call DeepSeek, Poe, OpenAI, Hugging Face, AkShare, Yahoo
Finance, or broker APIs unless you run the opt-in commands below.

## Contributor Entry Points

Small, reviewable contributions are the intended path for outside users:

- Start with the task list in
  [`docs/community_tasks.md`](docs/community_tasks.md).
- Create a plugin with
  `tradearena new-plugin --type risk --name max-drawdown-guard`.
- Follow the plugin contracts in
  [`docs/plugin_development.md`](docs/plugin_development.md).
- Submit redacted benchmark rows through
  [`docs/benchmark_submissions.md`](docs/benchmark_submissions.md).
- Use the challenge format in
  [`docs/benchmark_challenges.md`](docs/benchmark_challenges.md) for
  reproducible comparisons.

## LLM Run Paths

Live provider calls are opt-in.

- `tradearena --benchmark tradearena-core` runs the deterministic smoke test.
- `python examples/llm_cache_replay_demo.py` shows a redacted manifest from
  prior LLM runs without storing raw prompts or responses.
- `tradearena --benchmark llm-smoke ...` runs one live or cache-backed LLM
  analyst case.
- `tradearena --paper-output ...` runs the larger experiment suite. LLM sections
  use cache-first behavior where configured.

One real provider-backed smoke baseline is tracked here:
[`docs/results/llm_live_baseline.md`](docs/results/llm_live_baseline.md).
It records a 2026-05-18 Poe-hosted `gpt-5.5` run with redacted cache manifests
and no raw prompt/response text in Git.

Minimal live LLM smoke test through Poe:

```powershell
$env:POE_API_KEY="..."
tradearena --benchmark llm-smoke `
  --analysts poe-llm `
  --llm-model gpt-5.5 `
  --periods 3 `
  --symbols SYN,ALT `
  --llm-cache outputs/examples/poe_llm_smoke_cache.jsonl
```

Minimal live LLM smoke test through DeepSeek:

```powershell
$env:DEEPSEEK_API_KEY="..."
tradearena --benchmark llm-smoke `
  --analysts deepseek-llm `
  --llm-model deepseek-v4-flash `
  --periods 3 `
  --symbols SYN,ALT `
  --llm-cache outputs/examples/deepseek_llm_smoke_cache.jsonl
```

These commands write cache entries locally. Git ignores the cache because raw
prompts and responses can contain provider, licensing, privacy, or portfolio
constraints.

## Advanced Integrations Safety

DeepSeek, Poe-hosted models, OpenAI-compatible chat endpoints, AkShare, Yahoo
Finance, and broker-facing workflows are opt-in advanced paths. They are not
part of the first-run command.

- Keep provider keys in environment variables or an OS secret manager.
- Track metrics and redacted manifests, not raw prompt/response caches.
- For Yahoo Finance or AkShare downloads, record source, frequency, symbols,
  timestamp policy, and adjustment mode.
- Treat the execution model as a stress model unless quote/fill logs are used
  for calibration.
- Broker-facing examples must stay paper-only or human-reviewed. The default
  examples do not submit live orders.

Do not commit `.env` files, provider JSONL caches, broker tokens, account
statements, or private holdings. If a run needs to be shared, publish a redacted
submission or cache manifest instead of raw provider text.

The full checklist is in
[`docs/advanced_integrations_security.md`](docs/advanced_integrations_security.md).

## Install And Run

From a clone:

```bash
python -m pip install -e ".[dev]"
tradearena --benchmark tradearena-core
python -m tradearena.cli --benchmark tradearena-core
```

From GitHub without cloning first:

```bash
python -m pip install "git+https://github.com/weich97/TradeArena.git"
tradearena --benchmark tradearena-core
```

## Benchmark Result

The v0.1 benchmark card makes one limited claim:

> LLM trading-agent results can change materially once risk gates and
> paper-execution costs are included.

The public leaderboard includes two tracked model comparisons:

- a 42-row synthetic matrix: seven LLMs across calm-trend, high-volatility,
  jump/tail, liquidity-collapse, spread-explosion, and latency-spike
  scenarios;
- a 14-row real-market matrix: the same seven models across Yahoo Finance
  `^GSPC`, `BTC-USD`, and CME Bitcoin futures (`BTC=F`) windows.

Models include Poe-hosted `gpt-5.5`, `gemini-3.1-pro`, `kimi-k2.5`, `glm-5`,
`claude-opus-4.7`, plus direct `deepseek-v4-flash` and `deepseek-v4-pro`.
The rows are redacted benchmark manifests; raw provider prompts and responses
remain in ignored local caches.

Open:

- Static page:
  [`weich97.github.io/TradeArena/benchmark-v0.1.html`](https://weich97.github.io/TradeArena/benchmark-v0.1.html)
- Leaderboard:
  [`weich97.github.io/TradeArena/community_registry.html`](https://weich97.github.io/TradeArena/community_registry.html)
- Markdown artifact:
  [`docs/results/benchmark_v0_1.md`](docs/results/benchmark_v0_1.md)
- Model matrix:
  [`docs/results/model_matrix/leaderboard_model_matrix.md`](docs/results/model_matrix/leaderboard_model_matrix.md)
- Real-market matrix:
  [`docs/results/real_market_matrix/real_market_model_matrix.md`](docs/results/real_market_matrix/real_market_model_matrix.md)

Rebuild:

```bash
python scripts/build_benchmark_page.py
python scripts/run_leaderboard_model_matrix.py --update-registry
python scripts/run_real_market_leaderboard.py --update-registry
```

## Benchmark Maturity

Before calling TradeArena an externally validated community benchmark, three
pieces still need to exist: a stable academic report, independent validation
reports, and non-maintainer contributions that are reviewed in public.

- Maturity track: [`docs/benchmark_maturity.md`](docs/benchmark_maturity.md)
- Academic report plan: [`docs/academic_report_plan.md`](docs/academic_report_plan.md)
- External validation protocol: [`docs/external_validation.md`](docs/external_validation.md)
- Community participation rules:
  [`docs/community_participation.md`](docs/community_participation.md)

## Validate A Redacted Benchmark Row

TradeArena can validate redacted benchmark manifests. A manifest shares the
scenario, execution settings, risk settings, metrics, and reproducibility hash.
It should not expose raw provider prompts, raw responses, credentials, or
private portfolios. The format is for research exchange; one maintainer-authored
manifest is not community adoption.

```bash
tradearena validate-submission examples/benchmark_submissions/example_redacted_submission.json
tradearena hash-run outputs/examples/audit_walkthrough_trajectory.json
```

See [`docs/benchmark_submissions.md`](docs/benchmark_submissions.md).

## Visual Preview

<table>
  <tr>
    <th>Audit lifecycle</th>
    <th>Execution stress</th>
    <th>Diagnostic loop</th>
  </tr>
  <tr>
    <td>
      <img src="docs/assets/readme_audit_lifecycle.gif"
           alt="Animated observe-plan-risk-execute-reflect audit trace"
           width="280">
    </td>
    <td>
      <img src="docs/assets/readme_execution_realism.gif"
           alt="Animated execution comparison of ideal, realistic, high-spread,
                low-liquidity, and high-latency fills"
           width="280">
    </td>
    <td>
      <img src="docs/assets/readme_diagnostics_loop.gif"
           alt="Animated representation, risk-feedback, and concentration diagnostics"
           width="280">
    </td>
  </tr>
</table>

The browser-playable demo video is here:
[`weich97.github.io/TradeArena/demo_video.html`](https://weich97.github.io/TradeArena/demo_video.html).

## What Is In The Repo

- A runner that records market observations, agent decisions, risk reports,
  simulated fills, portfolio state, and metrics.
- A paper-execution simulator with fees, spread, slippage, latency, liquidity
  caps, partial fills, and rejections.
- A risk manager with pre-trade clipping/blocking, in-trade warnings, and
  post-trade attribution.
- Extension points for data providers, analysts, strategies, risk managers,
  simulators, memory stores, planners, and evaluators.
- A schema for redacted benchmark manifests and a small registry builder.

## Extension Path

Start with one small plugin:

```bash
python examples/custom_plugin_demo.py
python examples/extension_walkthrough_demo.py
```

The walkthrough swaps in a custom analyst, risk manager, and evaluator while the
rest of the runner stays unchanged.

Useful entry points:

- [`examples/README.md`](examples/README.md)
- [`docs/demo_matrix.md`](docs/demo_matrix.md)
- [`docs/extension_walkthrough.md`](docs/extension_walkthrough.md)
- [`docs/plugin_development.md`](docs/plugin_development.md)
- [`plugins/README.md`](plugins/README.md)
- [`docs/contributor_roadmap.md`](docs/contributor_roadmap.md)

## Documentation Map

- Quickstart: [`docs/getting_started.md`](docs/getting_started.md)
- Advanced integration safety:
  [`docs/advanced_integrations_security.md`](docs/advanced_integrations_security.md)
- Technical white paper: [`docs/technical_report.md`](docs/technical_report.md)
- Benchmark maturity:
  [`docs/benchmark_maturity.md`](docs/benchmark_maturity.md)
- Academic report plan:
  [`docs/academic_report_plan.md`](docs/academic_report_plan.md)
- External validation:
  [`docs/external_validation.md`](docs/external_validation.md)
- Community participation:
  [`docs/community_participation.md`](docs/community_participation.md)
- Contributor tasks:
  [`docs/community_tasks.md`](docs/community_tasks.md)
- Plugin development:
  [`docs/plugin_development.md`](docs/plugin_development.md)
- Benchmark challenges:
  [`docs/benchmark_challenges.md`](docs/benchmark_challenges.md)
- Community operations:
  [`docs/community_operations.md`](docs/community_operations.md)
- Market rules and stress presets:
  [`docs/market_rules.md`](docs/market_rules.md)
- Observability:
  [`docs/observability.md`](docs/observability.md)
- Schemas: [`docs/schemas.md`](docs/schemas.md)
- Execution model: [`docs/execution_model.md`](docs/execution_model.md)
- Benchmark submissions: [`docs/benchmark_submissions.md`](docs/benchmark_submissions.md)
- Related work: [`docs/related_work.md`](docs/related_work.md)
- Retail planning sandbox: [`docs/retail_planning.md`](docs/retail_planning.md)
- Research protocol: [`docs/research_protocol.md`](docs/research_protocol.md)
- Security policy: [`SECURITY.md`](SECURITY.md)
- Governance: [`GOVERNANCE.md`](GOVERNANCE.md)

## Local Checks

Each checkout can use its own `.venv`, which helps if you keep public and
private copies of the project side by side:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_local.ps1
```

The script installs the checkout in editable mode, then runs compile checks,
Ruff, tests, release-readiness checks, submission validation, artifact-contract
validation, and JSON validation.

## Safety Boundary

TradeArena does not promise profitable trading, does not provide financial
advice, and does not execute live trades by default. Public examples are
offline, paper-only, or human-review oriented. Broker and provider integrations
must follow [`docs/advanced_integrations_security.md`](docs/advanced_integrations_security.md),
[`SECURITY.md`](SECURITY.md), and [`GOVERNANCE.md`](GOVERNANCE.md).

## Cite

See [`CITATION.cff`](CITATION.cff). If you use TradeArena in research or
software, cite the repository release you used.
