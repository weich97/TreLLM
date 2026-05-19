# Benchmark Submissions

TradeArena accepts redacted benchmark manifests so users can compare runs
without sharing raw provider prompts, responses, credentials, or private
portfolio data.

## Validate One Submission

```bash
tradearena validate-submission examples/benchmark_submissions/example_redacted_submission.json
```

Equivalent script entry:

```bash
python scripts/validate_benchmark_submission.py examples/benchmark_submissions/example_redacted_submission.json
```

## Build The Registry

```bash
tradearena build-registry examples/benchmark_submissions \
  --output docs/results/community_registry.md \
  --csv-output docs/results/community_registry.csv \
  --html-output docs/results/community_registry.html
```

The generated registry is tracked at
[`docs/results/community_registry.md`](results/community_registry.md).
The browser-readable version is
[`docs/results/community_registry.html`](results/community_registry.html).
Challenge format, leaderboard badges, anonymous rows, and citation guidance are
defined in [`docs/benchmark_challenges.md`](benchmark_challenges.md).

The registry format is designed for both deterministic baselines and redacted
LLM policy runs. Public submissions can include provider family, public-safe
model display name, prompt mode, risk-feedback mode, parse coverage, metrics,
and hashes for derived artifacts while still omitting raw prompts and responses.
See:

- [`examples/benchmark_submissions/example_redacted_submission.json`](../examples/benchmark_submissions/example_redacted_submission.json)
- [`examples/benchmark_submissions/example_llm_redacted_submission.json`](../examples/benchmark_submissions/example_llm_redacted_submission.json)
- [`schemas/benchmark_submission.schema.json`](../schemas/benchmark_submission.schema.json)

## Hash A Trajectory

```bash
tradearena hash-run outputs/examples/audit_walkthrough_trajectory.json
```

The hash is computed from stable scenario, data, execution, risk, agent,
redaction, and trajectory-manifest fields. Outcome metrics are intentionally
excluded so the fingerprint identifies the reproducible run context rather than
the score.

## Safety Boundary

Submissions should include:

- redacted model metadata,
- prompt mode, parse coverage, and risk feedback mode when an LLM is involved,
- execution and risk configuration,
- compact metrics,
- trajectory manifest path or URI plus public artifact hashes,
- reproducibility hash.

Submissions should not include:

- API keys or broker credentials,
- raw model prompts or responses,
- private holdings,
- live-order instructions.

## Privacy And Reproducibility Tradeoff

The registry is intentionally not a raw trajectory warehouse. It preserves
enough metadata to compare audit-ready runs and detect duplicate submissions,
but it does not require providers, researchers, or users to publish raw prompts,
raw completions, exact private holdings, or credentials. The reproducibility
hash covers scenario, data, agent/config, risk, execution, redaction, and
manifest identity; outcome metrics are excluded so a score change does not
rewrite the run identity.
