# Community Benchmark Registry

This registry is generated from redacted benchmark submission manifests.
It is designed to compare audit-ready runs without exposing raw provider
prompts, responses, private portfolios, or credentials.

| Entry | Scenario | Agent | Prompt | Feedback | Parse | Data | Return | Max DD | Fill | Rejected | Risk edits | Audit | Badges | Hash |
| --- | --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| ta-aad1948b44bf | crisis_scene_llm_redacted_example | poe / frontier-chat-model-redacted | rationale | true | 0.9670 | yahoo-finance-csv (hourly, 3 symbols) | 0.0108 | -0.0187 | 0.7816 | 28 | 196 | 1.0000 | Reproducible; Redacted | `sha256:aad1948b44b...` |
| ta-ed2d5e4f2ff3 | quickstart_core_synthetic_v0_1 | deterministic / signal-weighted-baseline | none | true | 1.0000 | synthetic-market (daily, 2 symbols) | 0.3508 | -0.0126 | 0.9034 | 14 | 124 | 1.0000 | Reproducible; Redacted | `sha256:ed2d5e4f2ff...` |

## Submission Rules

- Submit redacted manifests, not raw model prompt/response caches.
- Do not include broker credentials, API keys, or private holdings.
- Keep `reproducibility_hash` stable for the same scenario, data,
  execution config, risk config, agent metadata, and trajectory manifest.
