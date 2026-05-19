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

## Good First Issues

| Task | Suggested labels | Expected validation |
| --- | --- | --- |
| Add an SMA crossover strategy plugin | `good first issue`, `help wanted` | `pytest` for deterministic target weights |
| Add a max-drawdown risk preset | `good first issue`, `risk` | one fixture where decisions are blocked after drawdown |
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
| Add a black-swan liquidity halt scenario | `help wanted`, `risk`, `benchmark` | fixture with rejected or delayed orders |

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
