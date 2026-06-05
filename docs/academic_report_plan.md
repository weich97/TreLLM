# Academic Report Plan

The public technical report is now available as:

> Weicheng Xue. 2026. Representation Signatures and Risk-Feedback Alignment in
> LLM Trading Agents. arXiv:2605.28850.
> https://arxiv.org/abs/2605.28850

See [`docs/research_report.md`](research_report.md) for citation metadata.

TreLLM currently has technical documentation and TradeArena leaderboard
artifacts. A credible academic report needs a narrower scientific argument,
explicit evidence, and limitations that a reviewer can audit.

## Report Positioning

Recommended framing:

> We study how autonomous financial-agent intent changes when structured risk feedback
> and execution frictions are made observable, replayable, and externally
> auditable.

The broader project framing should be agent reliability, risk-aware AI systems,
and intent-to-execution audit. Trading is the current high-stakes experimental
domain, but the research object is how autonomous financial agents transform
intent into constrained, executable actions.

Avoid framing the paper as "we built a tool" unless the venue is explicitly an
artifact, systems, or benchmark track. The framework is the experimental
substrate; the paper should emphasize measurable behavior, failure modes,
calibration limits, and reproducibility.

## Minimum Report Contents

| Section | Required evidence |
| --- | --- |
| Abstract and introduction | One scientific claim, one benchmark claim, one limitation sentence |
| Related work | Trading backtesters, execution simulation, agent benchmarks, LLM evaluation, financial RL |
| System description | Architecture diagram, reliability lifecycle, risk lifecycle, execution equation, trajectory schema |
| Experiments | Deterministic baseline, provider-backed LLM baseline, risk-feedback ablation, execution stress, representation diagnostics |
| External validation | Independent reproduction or calibration reports, not only maintainer-generated artifacts |
| Limitations | Provider routing, synthetic data, OHLCV-only execution calibration, private-fill availability |
| Reproducibility appendix | Commit hash, commands, package versions, data sources, redaction policy |

## Claim Ladder

Use this ladder to avoid overclaiming:

| Claim level | Acceptable statement | Required support |
| --- | --- | --- |
| Prototype | TreLLM can run auditable offline and paper/sandbox agent loops | CI, tests, deterministic smoke artifacts |
| Benchmark | TradeArena can compare agents under shared risk and execution assumptions | Reproducible metrics, schema validation, benchmark rows |
| Scientific | Structured risk feedback changes LLM decision behavior | Multiple models, ablations, confidence intervals, external validation |
| Execution realism | The simulator approximates realized trading costs | Quote/fill-log calibration against private or licensed fills |

The current public repository is strongest at the prototype and early benchmark
levels. Scientific and execution-realism claims need the external validation
track before they should be stated strongly.

## Result Artifacts

A report-ready run should archive:

- `tables/metrics.csv` and `tables/metrics.md`;
- `tables/equity_curves.csv`;
- `tables/execution_events.csv`;
- `tables/risk_events.csv`;
- `charts/*.svg`;
- redacted LLM cache manifests;
- `summary.json`;
- environment metadata and commit hash;
- any external validation issue or pull request link.

Do not include raw provider prompts, raw provider responses, credentials, broker
statements, or private holdings in a public paper artifact.

## Review Checklist

Before submitting the report:

- Every table and figure points to a reproducible script or tracked artifact.
- Every live API result has a cache or redacted manifest.
- Every execution-realism statement says whether it is stress-based or
  fill-calibrated.
- Synthetic data claims are separated from historical-data claims.
- External validation is clearly labeled as independent, pending, or unavailable.
- The paper does not describe repository mechanics such as how a PDF zip was
  generated.
