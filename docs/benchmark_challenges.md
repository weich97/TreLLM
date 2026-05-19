# Benchmark Challenges

Benchmark challenges are a lightweight way to compare agents without requiring
participants to reveal prompts, private holdings, or provider credentials.

## Challenge Format

Each challenge should publish:

- a scenario identifier and version;
- data source, date range, frequency, and symbol universe;
- execution and risk configuration;
- allowed agent classes;
- required metrics;
- redaction rules;
- the command used to validate submissions.

Example:

```bash
tradearena build-registry examples/benchmark_submissions \
  --output docs/results/community_registry.md \
  --csv-output docs/results/community_registry.csv \
  --html-output docs/results/community_registry.html
```

## Public Leaderboard

The tracked leaderboard is generated from redacted manifests:

- Markdown: [`docs/results/community_registry.md`](results/community_registry.md)
- HTML: [`docs/results/community_registry.html`](results/community_registry.html)
- Multi-scenario LLM model matrix:
  [`docs/results/model_matrix/leaderboard_model_matrix.md`](results/model_matrix/leaderboard_model_matrix.md)
- Real-market Yahoo matrix:
  [`docs/results/real_market_matrix/real_market_model_matrix.md`](results/real_market_matrix/real_market_model_matrix.md)

The HTML page supports search, sortable columns, and row details. Each accepted
row carries a reproducibility badge when its manifest passes schema validation
and hash verification.

## Reproducibility Badge

Use the CLI to compute and publish stable run identity:

```bash
tradearena hash-run outputs/examples/audit_walkthrough_trajectory.json
tradearena validate-submission examples/benchmark_submissions/example_redacted_submission.json
```

Badge semantics:

| Badge | Meaning |
| --- | --- |
| `Reproducible` | manifest validated and reproducibility hash matched |
| `Redacted` | raw prompts, responses, secrets, and private holdings are absent |
| `Needs review` | schema passes but maintainer has not reviewed scenario fit |

## Anonymous And Named Tracks

Participants can submit either:

- named rows, where `agent.provider` and `agent.model_family` are public-safe;
- anonymous rows, where `model_identifier_redacted` is true and public identity
  is represented by a stable entry ID.

Anonymous rows still need enough metadata for comparison: prompt mode,
risk-feedback mode, parse coverage, execution config, risk config, data source,
metrics, trajectory manifest, and reproducibility hash.

## Citation Template

For an accepted row, cite the entry ID and manifest hash:

```text
TradeArena benchmark entry <ENTRY_ID>, scenario <SCENARIO_ID>,
manifest hash <REPRODUCIBILITY_HASH>, accessed <DATE>.
```

If a top-ranked row is later revised, keep both hashes. Do not overwrite the
history of a challenge after results are discussed publicly.

## Suggested Cadence

- Monthly smoke challenge: small scenario, deterministic or cache-backed,
  designed for newcomers.
- Quarterly research challenge: fixed historical window, explicit execution
  stress, redacted LLM or policy submissions allowed.
- Special stress challenge: liquidity halt, flash crash, rate-limit, or
  false-audit scenario for robustness studies.
