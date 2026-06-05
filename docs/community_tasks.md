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

New contributors can start with the shorter
[`external_validation_quickstart.md`](external_validation_quickstart.md), then
come back here when choosing a specific issue-sized task. For baseline rows,
use
[`deterministic_baseline_submission_quickstart.md`](deterministic_baseline_submission_quickstart.md).
For execution work,
use [`execution_calibration_quickstart.md`](execution_calibration_quickstart.md)
to pick the weakest honest evidence label and report fields. For wording and
claim checks, use
[`claim_boundary_review_quickstart.md`](claim_boundary_review_quickstart.md).

| Task | Time | Commands | Evidence to attach | Suggested labels |
| --- | ---: | --- | --- | --- |
| [Run v0.2 reproduction pack on macOS](https://github.com/weich97/TradeArena/issues/43) | 1 hour | `python scripts/run_external_reproduction_pack.py` | `outputs/reproduction/v0_2/manifest.json`, Python version, shell log, deviations | `validation`, `reproducibility`, `good first issue` |
| [Run v0.2 reproduction pack on Ubuntu](https://github.com/weich97/TradeArena/issues/44) | 1 hour | `python scripts/run_external_reproduction_pack.py` | same manifest plus distro, Python, and install notes | `validation`, `reproducibility`, `good first issue` |
| [Submit one deterministic baseline row](https://github.com/weich97/TradeArena/issues/46) | 1-2 hours | `python scripts/validate_benchmark_submission.py <row.json>`; `python scripts/build_benchmark_registry.py examples/benchmark_submissions` | one schema-valid deterministic manifest, rebuilt registry diff, and reproducibility hash | `benchmark`, `good first issue` |
| [Submit one quote/fill calibration mini-report](https://github.com/weich97/TradeArena/issues/47) | 2-3 hours | `python scripts/calibrate_quote_fill_model.py` or the Binance sample command in `docs/execution_calibration_quickstart.md` | calibration JSON/Markdown with source, venue, date range, sample size, replay error, and residuals | `execution`, `validation`, `help wanted` |
| [Review one benchmark claim boundary](https://github.com/weich97/TradeArena/issues/48) | 1 hour | `python scripts/check_release_readiness.py`; inspect `docs/claim_boundary_review_quickstart.md` | one issue or PR that maps a README/result claim to engineering, benchmark, or scientific evidence | `docs`, `discussion`, `validation` |

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

## Broker And Live-Ready Tracks

Each task should remain offline export, dry run, or paper sandbox by default.
Use [`live_trading_readiness.md`](live_trading_readiness.md#external-contribution-tracks)
and [`broker_adapter_contract.md`](broker_adapter_contract.md) as the review
boundary. No task in this table should introduce default live submission.

| Task | Suggested labels | Expected validation |
| --- | --- | --- |
| Add one broker adapter capability manifest check | `good first issue`, `broker`, `safety` | `tradearena validate-broker-capability outputs/examples/broker_capability_manifest/capability_manifest.json`; no default live submission |
| Add one approval-binding edge-case test | `good first issue`, `broker`, `risk` | `pytest tests/test_issue_demos.py -q` with a stale approval, mismatched request hash, disallowed symbol, or notional-limit case |
| Add one broker response status-mapping fixture | `help wanted`, `broker`, `execution` | schema-valid response artifact with accepted, rejected, partial-fill, cancel, or unknown status and recomputed reconciliation counts |
| Add one paper-sandbox adapter skeleton behind an optional dependency | `help wanted`, `adapter`, `paper-trading` | mocked CI test proving no default network call, `paper_sandbox` account mode, response artifact, and no committed credentials |
| Add an operator runbook checklist for live-capable paths | `docs`, `discussion`, `risk` | checklist naming kill switch, approval expiry, account mode, rollback, artifact retention, and incident owner |

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

Maintainer starter fixtures now exist for the first market-rule slice:

```bash
python examples/market_rules_fixture_demo.py
```

The command writes `docs/results/market_rules_fixture.json` and
`docs/results/market_rules_fixture.md`. External follow-up work should extend
the fixture with real exchange calendar assumptions or independently reviewed
venue-rule references rather than treating the starter fixture as complete
market coverage.
