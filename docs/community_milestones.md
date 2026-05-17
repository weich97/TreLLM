# Community Milestones

These milestones are the intended GitHub milestone structure for the public
repository. They are documented here so the roadmap stays visible even when a
contributor is reading the source tree rather than the GitHub Issues UI.

## v0.1.1: Reproducibility Polish

Goal: make the first public benchmark easier to cite, reproduce, and review.

- Add a high-spread execution stress preset with CSV, JSON, and SVG artifacts.
- Reflow public Markdown files for readable diffs.
- Add benchmark provenance and limitations blocks.
- Keep `https://weich97.github.io/TradeArena/` as a stable root landing page.
- Smoke-check the Colab and Codespaces paths.
- Keep release-readiness checks in CI.

## v0.2.0: Community Benchmark Registry

Goal: let external users submit comparable, redacted benchmark rows.

- Finalize `schemas/benchmark_submission.schema.json`.
- Add one example redacted benchmark submission.
- Build a static registry page from submitted manifests.
- Add one external baseline or scenario.
- Document review rules for provider-sensitive model outputs.

## Discussion Calls To Action

- Execution simulation: comment with the market-friction assumption you think
  matters most.
- Redacted benchmarks: comment with fields you would be comfortable sharing.
- Teaching or project use: post the scenario you want students or teammates to
  reproduce.
- New adapters: link the data, broker, or model interface you want TradeArena
  to support.
