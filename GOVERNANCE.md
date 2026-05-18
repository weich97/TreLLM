# Governance

TradeArena is maintained as an open benchmark and audit framework for financial
AI agents. The project prioritizes reproducibility, safe execution boundaries,
and reviewable artifacts over short-term performance claims.

## Version Policy

- `v0.x` APIs are experimental.
- Core schemas and protocol objects receive stricter review than examples.
- Examples may evolve quickly when they improve reproducibility or onboarding.

## Review Principles

- Core protocol changes should preserve replayable trajectories and audit logs.
- Provider adapters must avoid committing raw prompt/response caches.
- Broker or execution adapters must default to offline, paper-only, or
  human-approved behavior.
- New benchmark rows should include data/source notes, execution assumptions,
  risk assumptions, and a reproducibility hash.
- Advanced integrations must document their network calls, secret source,
  cache/redaction policy, and whether they can touch live accounts.
- First-run demos must remain no-key and must not depend on live model, data, or
  broker APIs.

## Advanced Integration Gate

Changes that add or expand DeepSeek, Poe, OpenAI-compatible, Yahoo Finance,
AkShare, broker, or account-data paths should be reviewed against this gate:

- the default code path is offline, cache replay, paper-only, or human-review;
- credentials are read from environment variables or an OS secret manager;
- generated raw caches and private data are ignored by Git;
- public docs state data provenance and execution-calibration limits;
- tests prove the default path does not submit live orders;
- redacted manifests are available when results need to be shared.

## Maintainer Decisions

Maintainers may reject contributions that blur the boundary between benchmark
research and live financial advice, expose credentials or private data, or make
unverifiable profitability claims.
