<p align="center">
  <img src="docs/assets/tradearena_wordmark.svg"
       alt="TradeArena wordmark"
       width="780">
</p>

<p align="center">
  <strong>
    Early-stage research prototype for studying LLM trading-agent behavior
    under explicit execution, risk, and replayability constraints.
  </strong>
</p>

<p align="center">
  <a href="https://github.com/weich97/TradeArena/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/weich97/TradeArena/actions/workflows/ci.yml/badge.svg">
  </a>
  <a href="https://github.com/weich97/TradeArena/actions/workflows/codeql.yml">
    <img alt="CodeQL" src="https://github.com/weich97/TradeArena/actions/workflows/codeql.yml/badge.svg">
  </a>
  <a href="https://github.com/weich97/TradeArena/releases/latest">
    <img alt="Release" src="https://img.shields.io/github/v/release/weich97/TradeArena">
  </a>
  <a href="https://pypi.org/project/tradearena-benchmark/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/tradearena-benchmark">
  </a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10--3.12-0f172a">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-f59e0b">
</p>

<p align="center">
  <a href="docs/getting_started.md">Getting started</a> |
  <a href="https://pypi.org/project/tradearena-benchmark/">PyPI</a> |
  <a href="https://weich97.github.io/TradeArena/">Project site</a> |
  <a href="https://weich97.github.io/TradeArena/benchmark-v0.1.html">Benchmark card</a> |
  <a href="docs/benchmark_submissions.md">Redacted manifests</a> |
  <a href="docs/demo_matrix.md">Demo matrix</a> |
  <a href="docs/contributor_roadmap.md">Roadmap</a> |
  <a href="SECURITY.md">Security</a>
</p>

# TradeArena

TradeArena is an early-stage research prototype that experiments with turning
trading-agent decisions into traceable trajectories:

```text
observation -> signal -> intended allocation -> risk gate -> order
  -> fill/rejection -> portfolio state -> diagnostic report
```

It is not a trading bot and not a mature production benchmark. The current
prototype asks a narrower research question: whether an LLM trading agent's
intent, risk interventions, execution effects, and diagnostic artifacts can be
captured clearly enough to support careful analysis.

## Technical Mechanics

TradeArena is organized as a deterministic agent loop. The runner in
[`src/tradearena/core/runner.py`](src/tradearena/core/runner.py) executes the
same lifecycle at every market timestamp:

```text
observe market snapshot
  -> collect analyst signals
  -> convert signals into target-weight decisions
  -> clip or block decisions with the risk manager
  -> convert approved targets into orders
  -> simulate fills under latency, liquidity, spread, slippage, and commission
  -> write risk reports, execution reports, memory events, and trajectory rows
```

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
a risk-off scale when recent memory contains drawdowns, rejected orders, or risk
violations. Classical baselines are also available, including equal
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

The simulator records requested quantity, filled quantity, fill ratio, latency,
liquidity available, commission, slippage cost, partial fills, pending orders,
and rejections in an `ExecutionReport`. Its default settings are transparent
stress-test assumptions, not a claim of broker-grade transaction-cost
calibration.

## Execution Calibration Boundary

Execution realism is only meaningful when its assumptions are visible. TradeArena
therefore separates the simulator equation from parameter calibration:

| Parameter | Default role | Calibration source needed |
| --- | --- | --- |
| `commission_bps` | explicit fee on traded notional | broker or exchange fee schedule |
| `spread_bps` | full quoted spread; market orders cross half | quote/NBBO or order-book snapshots |
| `base_slippage_bps` | residual shortfall before spread, impact, and bar volatility | historical order/fill logs |
| `participation_rate` | cap on fillable bar volume | execution policy or parent-order participation target |
| `latency_steps` | bar-delay before an order is eligible | submission, acknowledgement, and fill timestamps |
| `market_impact` | coefficient on participation | regression of implementation shortfall on participation |

The tracked Yahoo Finance OHLCV files can estimate bar range, tail range, dollar
volume, and participation-cap diagnostics. They cannot identify quoted spread,
queue depth, fee tier, latency, or realized shortfall. For that reason, current
example benchmark results should be read as execution-stress comparisons under
shared assumptions. Live-market execution claims require replacing the defaults
with quote/fill-calibrated parameters.

Run the diagnostic:

```bash
python scripts/calibrate_execution_model.py --data-dir data/real/yahoo_intraday_1h_50
```

This writes `docs/results/execution_calibration_intraday_1h.json` and
`docs/results/execution_calibration_intraday_1h.md`. Full details are in
[`docs/execution_model.md`](docs/execution_model.md).

Risk control is an auditable gate, not a hidden post-processing step.
[`MaxPositionRiskManager`](src/tradearena/agents/risk.py) runs three checks:

- pre-trade approval clips per-symbol weights to `max_abs_weight`, blocks
  decisions below `min_confidence`, rescales gross exposure above
  `max_gross_exposure`, and reports projected turnover above
  `max_single_step_turnover`;
- in-trade monitoring checks realized participation, latency, and slippage
  against `max_order_participation`, `max_latency_steps`, and
  `max_slippage_bps`;
- post-trade attribution reports realized PnL, commission, slippage cost, and
  final exposures.

Every intervention is serialized as a `RiskReport` with `RiskCheck` and
`RiskViolation` records. The trajectory therefore preserves both the model's
original intent and the executable decision after risk feedback, which is the
core substrate for risk-feedback, representation-drift, and hallucination-audit
experiments.

## Quick Start: Deterministic Smoke Test

```bash
python -m pip install tradearena-benchmark
tradearena --benchmark tradearena-core
```

This default command intentionally does **not** call an LLM. It is a no-key
smoke test for the runner, trajectory schema, risk gate, execution simulator,
and metric stack. It uses deterministic analysts so every new checkout can pass
CI-style validation before provider keys, model routing, or billing enter the
loop.

The PyPI distribution is `tradearena-benchmark` because `tradearena` is already
occupied on PyPI by an unrelated project. The import namespace and CLI remain
`tradearena`.

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
```

The first-run path uses deterministic agents, tracked snapshots, and local demo
artifacts. It does not call DeepSeek, Poe, OpenAI, Hugging Face, AkShare, Yahoo
Finance, or broker APIs unless you opt into the model or data commands below.

## LLM Run Paths

TradeArena supports LLM trading-agent experiments, but the repository keeps live
provider calls out of the default path. Use the path that matches what you want
to verify:

| Path | Calls an LLM? | Purpose |
| --- | --- | --- |
| `tradearena --benchmark tradearena-core` | No | Deterministic smoke test for core mechanics |
| `python examples/llm_cache_replay_demo.py` | No | Redacted manifest of prior LLM experiment coverage; no raw prompts or responses |
| `tradearena --benchmark llm-smoke ...` | Yes, unless a matching cache row exists | Minimal live/cache-backed LLM analyst run |
| `tradearena --paper-output ...` | Optional | Larger paper-grade suite with cache-first LLM sections |

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

These commands run one LLM analyst case and write cache entries locally. The
cache is deliberately ignored by Git because raw prompts and responses can carry
provider, licensing, privacy, or portfolio constraints.

## Advanced Integrations Safety

DeepSeek, Poe-hosted models, OpenAI-compatible chat endpoints, AkShare, Yahoo
Finance, and broker-facing workflows are opt-in advanced paths. They are not
part of the first-run command, and they must stay inside an explicit audit
boundary:

| Surface | Default boundary | Public artifact policy |
| --- | --- | --- |
| LLM providers | Environment-variable keys, cache-first replay, signals only | Track metrics and redacted manifests, not raw prompt/response caches |
| Yahoo Finance / AkShare | Download to normalized OHLCV CSV with source metadata | Record source, frequency, symbols, timestamp policy, and adjustment mode |
| Execution model | Stress assumptions unless calibrated with quote/fill logs | State parameter sources; do not call bar-only diagnostics broker-grade |
| Broker adapters | Paper export or human-review sandbox only | No live submission in default examples; no credentials in artifacts |

Use per-session environment variables or an OS secret manager. Do not commit
`.env` files, provider JSONL caches, broker tokens, account statements, or
private holdings. If a run needs to be shared, publish a redacted submission or
cache manifest instead of raw provider text.

The full checklist is in
[`docs/advanced_integrations_security.md`](docs/advanced_integrations_security.md).

No local install yet?

<p>
  <a href="https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=weich97/TradeArena">
    <img alt="Open in GitHub Codespaces"
         src="https://img.shields.io/badge/Open%20in-Codespaces-181717?logo=github">
  </a>
  <a href="https://colab.research.google.com/github/weich97/TradeArena/blob/main/notebooks/tradearena_5min_colab.ipynb">
    <img alt="Open in Colab"
         src="https://colab.research.google.com/assets/colab-badge.svg">
  </a>
</p>

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

The v0.1 benchmark card makes one compact claim:

> LLM trading-agent evaluation changes materially once intended allocations
> pass through auditable risk gates and explicit execution-stress constraints.

Open:

- Static page:
  [`weich97.github.io/TradeArena/benchmark-v0.1.html`](https://weich97.github.io/TradeArena/benchmark-v0.1.html)
- Markdown artifact:
  [`docs/results/benchmark_v0_1.md`](docs/results/benchmark_v0_1.md)

Rebuild:

```bash
python scripts/build_benchmark_page.py
```

## Validate A Redacted Benchmark Row

TradeArena can validate redacted benchmark manifests. They share scenario,
execution, risk, metrics, and reproducibility metadata without exposing raw
provider prompts, responses, credentials, or private portfolios. This is a local
research artifact format, not an adoption signal.

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

## What TradeArena Provides

| Need | TradeArena surface |
| --- | --- |
| Replayable decisions | Trajectory logs with prompts, memory digests, risk reports, fills, and metrics |
| Execution stress model | Configurable fees, spread, slippage, latency, liquidity caps, partial fills, rejections, and calibration diagnostics |
| Risk-aware evaluation | Pre-trade gates, in-trade monitors, post-trade attribution, violations |
| Extensibility | Data, analyst, strategy, risk, simulator, memory, planner, evaluator plugins |
| Redacted benchmark manifests | Manifest schema, registry builder, reproducibility hashes |

## Extension Path

Start with one small plugin:

```bash
python examples/custom_plugin_demo.py
python examples/extension_walkthrough_demo.py
```

The walkthrough swaps in a custom analyst, risk manager, and evaluator while
reusing the existing runner, data provider, strategy, execution simulator,
memory store, trajectory logger, and metric stack.

Useful entry points:

- [`examples/README.md`](examples/README.md)
- [`docs/demo_matrix.md`](docs/demo_matrix.md)
- [`docs/extension_walkthrough.md`](docs/extension_walkthrough.md)
- [`docs/contributor_roadmap.md`](docs/contributor_roadmap.md)

## Documentation Map

- Quickstart: [`docs/getting_started.md`](docs/getting_started.md)
- Advanced integration safety:
  [`docs/advanced_integrations_security.md`](docs/advanced_integrations_security.md)
- Technical white paper: [`docs/technical_report.md`](docs/technical_report.md)
- Schemas: [`docs/schemas.md`](docs/schemas.md)
- Execution model: [`docs/execution_model.md`](docs/execution_model.md)
- Benchmark submissions: [`docs/benchmark_submissions.md`](docs/benchmark_submissions.md)
- Related work: [`docs/related_work.md`](docs/related_work.md)
- Retail planning sandbox: [`docs/retail_planning.md`](docs/retail_planning.md)
- Research protocol: [`docs/research_protocol.md`](docs/research_protocol.md)
- Security policy: [`SECURITY.md`](SECURITY.md)
- Governance: [`GOVERNANCE.md`](GOVERNANCE.md)

## Local Checks

Each checkout can use its own `.venv`, so public and private repos do not
fight over editable installs:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_local.ps1
```

The script installs the current checkout in editable mode, runs compile checks,
Ruff critical checks, tests, release-readiness checks, submission validation,
artifact-contract validation, and JSON validation.

## Safety Boundary

TradeArena does not promise profitable trading, does not provide financial
advice, and does not execute live trades by default. Public examples are
offline, paper-only, or human-review oriented. Broker and provider integrations
must follow [`docs/advanced_integrations_security.md`](docs/advanced_integrations_security.md),
[`SECURITY.md`](SECURITY.md), and [`GOVERNANCE.md`](GOVERNANCE.md).

## Cite

See [`CITATION.cff`](CITATION.cff). If you use TradeArena in research or
software, cite the repository release you used.
