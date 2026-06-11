# TreLLM v0.3 Direct API Matrix Gate

This artifact verifies whether direct API model rows satisfy the v0.3 seed/sample threshold for main-paper scientific comparisons.
It does not run provider calls and does not promote fixture rows to model-performance evidence.

- Protocol: `trellm-v0.3-iclr-protocol`
- Rows: `4`
- Valid rows: `4`
- Coverage groups: `1`
- Main-threshold groups: `0`
- Headline scientific claim ready: `False`
- Claim boundary: This gate verifies direct API row provenance and seed/sample coverage. Rows tagged as protocol fixtures or below the threshold remain pilot evidence.
- Open-gap policy: The direct_api_model_matrix gap remains open until at least one non-fixture direct API group meets the v0.3 threshold of 10 seeds and 3 samples per seed.

## Coverage Groups

| Provider | Model | Scenario | Tier | Execution | Rows | Seeds | Min samples/seed | Main threshold | Blocking reasons |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| fixture-direct-api | fixture-llm-policy-v0 | synthetic_calm_trend_c0_v0_3 | C0 | E1 | 4 | 2 observed / 0 eligible | 2 observed / 0 eligible | false | fixture_provider_or_manifest_claim;insufficient_samples_per_seed;insufficient_seed_count;protocol_fixture_not_scientific_model_evidence |
