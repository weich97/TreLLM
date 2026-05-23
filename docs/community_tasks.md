# Contributor Task Backlog

This page turns the roadmap into small, reviewable work items. Each task should
fit in one focused PR with one validation command.

## Label Policy

| Label | Meaning |
| --- | --- |
| `good first issue` | Small scope, offline-friendly, and reviewable without domain expertise |
| `help wanted` | Maintainer wants outside input or implementation help |
| `discussion` | Needs design agreement before code |
| `benchmark` | Affects benchmark scenarios, manifests, registry, or metrics |
| `risk` | Affects risk checks, stress tests, or risk reports |
| `execution` | Affects order simulation, fills, fees, latency, or liquidity |
| `docs` | Documentation-only or documentation-first work |

## External Evidence Tasks

These five tasks are the preferred first contributions because they strengthen
the benchmark evidence chain: a non-maintainer can run it, question it, or
submit a comparable result. Each task should take about 1-3 hours and can be
filed through the external validation issue template or a small pull request.

| Task | Time | Commands | Evidence to attach | Suggested labels |
| --- | ---: | --- | --- | --- |
| [Run v0.2 reproduction pack on macOS](https://github.com/weich97/TradeArena/issues/43) | 1 hour | `python scripts/run_external_reproduction_pack.py` | `outputs/reproduction/v0_2/manifest.json`, Python version, shell log, deviations | `validation`, `reproducibility`, `good first issue` |
| [Run v0.2 reproduction pack on Ubuntu](https://github.com/weich97/TradeArena/issues/44) | 1 hour | `python scripts/run_external_reproduction_pack.py` | same manifest plus distro, Python, and install notes | `validation`, `reproducibility`, `good first issue` |
| [Submit one deterministic baseline row](https://github.com/weich97/TradeArena/issues/46) | 1-2 hours | `python scripts/run_classical_baseline_matrix.py`; `tradearena validate-submission <row.json>` | one schema-valid deterministic manifest, rebuilt registry diff, and reproducibility hash | `benchmark`, `good first issue` |
| [Submit one quote/fill calibration mini-report](https://github.com/weich97/TradeArena/issues/47) | 2-3 hours | `python scripts/calibrate_quote_fill_model.py` or the Binance sample command in `docs/execution_model_boundaries.md` | calibration JSON/Markdown with source, venue, date range, sample size, replay error, and residuals | `execution`, `validation`, `help wanted` |
| [Review one benchmark claim boundary](https://github.com/weich97/TradeArena/issues/48) | 1 hour | `python scripts/check_release_readiness.py`; inspect `docs/claim_boundaries.md` | one issue or PR that maps a README/result claim to engineering, benchmark, or scientific evidence | `docs`, `discussion`, `validation` |

Acceptance is deliberately narrow: one environment report, one row, one
calibration report, or one claim critique. This keeps external validation
reviewable without asking newcomers to understand the whole codebase.

## Good First Issues

| Task | Suggested labels | Expected validation |
| --- | --- | --- |
| Add an SMA crossover strategy plugin | `good first issue`, `help wanted` | `pytest` for deterministic target weights |
| Add a drawdown recovery chart to the showcase | `good first issue`, `risk`, `docs` | one fixture where kill-switch events are visible |
| Add an anonymous benchmark manifest example | `good first issue`, `docs`, `benchmark` | `tradearena validate-submission ...` |
| Add an Ollama local-model config example | `good first issue`, `docs` | cache-backed smoke command with no secrets |
| Improve alt text for generated HTML reports | `good first issue`, `docs` | inspect rebuilt HTML artifacts |
| Add a notebook cell that hashes a trajectory | `good first issue`, `docs` | run the notebook or the equivalent CLI command |

## Finance And Market Realism

| Task | Suggested labels | Expected validation |
| --- | --- | --- |
| Add A-share T+1 and price-limit scenario coverage | `help wanted`, `risk` | deterministic fixture with blocked same-day sell |
| Add HK lot-size and trading-calendar demo | `help wanted`, `benchmark` | example run plus documented assumptions |
| Add crypto fee-tier and spread-shock preset | `help wanted`, `execution` | stress example with changed fill costs |
| Add an Almgren-Chriss impact stress plugin | `help wanted`, `execution`, `discussion` | compare modeled shortfall on a small fixture |
| Calibrate liquidity-shock presets against fill logs | `help wanted`, `risk`, `benchmark` | compare tracked shock rows with venue or broker fill data |

## Benchmark Flywheel

| Task | Suggested labels | Expected validation |
| --- | --- | --- |
| Add reproducibility badge checks to registry rows | `help wanted`, `benchmark` | `tradearena build-registry examples/benchmark_submissions` |
| Add row-level detail panels to the leaderboard | `good first issue`, `benchmark` | open generated `community_registry.html` |
| Add a quarterly challenge seed file | `help wanted`, `benchmark` | documented command and expected artifact paths |
| Add a redacted citation entry template | `good first issue`, `docs` | schema validation still passes |

## Observability

| Task | Suggested labels | Expected validation |
| --- | --- | --- |
| Export trajectory events to OpenTelemetry spans | `help wanted`, `discussion` | local JSON or console exporter test |
| Export metrics to W&B or MLflow with opt-in dependency | `help wanted`, `discussion` | mock-backed test, no live service required |
| Map trajectory records to OpenAI Evals or LangSmith-style traces | `help wanted`, `discussion` | schema example and conversion test |

For issue bodies, copy the task row, add a file path owner, and name the command
that a reviewer should run.
