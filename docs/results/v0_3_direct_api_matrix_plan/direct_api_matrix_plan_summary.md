# TreLLM v0.3 Direct API Matrix Plan

This artifact pre-registers the direct API call matrix and checks whether required credential environment variables are present.
It does not make provider calls and does not count as model-performance evidence.

- Protocol: `trellm-v0.3-iclr-protocol`
- Planned rows: `30`
- Coverage groups: `1`
- Threshold-target groups: `1`
- Ready groups: `0`
- Ready to run: `False`
- Claim boundary: This is a pre-registered direct API matrix plan and credential preflight, not model-performance evidence. The direct_api_model_matrix gap remains open until non-fixture provider manifests and submissions pass the matrix gate.

## Coverage Groups

| Provider | Model | Scenario | Tier | Execution | Rows | Seeds | Min samples/seed | Env var | Env present | Status | Blocking reasons |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| openai | gpt-5.5 | synthetic_calm_trend_c0_v0_3 | C0 | E1 | 30 | 10 | 3 | OPENAI_API_KEY | false | blocked | credential_env_var_missing |
