# TreLLM v0.3 Evidence Index

This index maps generated public artifacts to the v0.3 ICLR protocol claims.
It is deliberately conservative: fixture and pilot artifacts do not support headline scientific model-performance claims.

- Protocol: `trellm-v0.3-iclr-protocol`
- Present artifacts: `8 / 8`
- Public-artifact-covered protocol artifacts: `12 / 13`
- Fixture-covered protocol artifacts: `8 / 13`
- Open gaps: `2`
- Headline scientific claim ready: `False`
- Claim boundary: This index maps public v0.3 artifacts to protocol claims. Current artifacts validate protocol plumbing and pilot mechanisms; they do not yet support headline scientific model-performance claims.

## Artifact Map

| Artifact | Claim area | Stage | Methods | Supports headline claim | Status |
| --- | --- | --- | --- | --- | --- |
| direct_api_pilot | direct API provenance | protocol-fixture | seed/sample manifest coverage | false | present |
| direct_api_matrix_gate | direct API model matrix threshold gate | threshold-gate | direct_manifest_hash_binding;seed_sample_threshold_gate | false | present |
| direct_api_model_matrix_plan | direct API model matrix run plan and credential preflight | planning-note | pre_registered_10x3_matrix_plan;credential_env_var_preflight | false | present |
| execution_ladder | execution assumption sensitivity | protocol-fixture | kendall_tau;top_k_jaccard;bootstrap_ci | false | present |
| finaudit_pilot | financial trace audit | protocol-fixture | precision;recall;f1;wilson_interval;difficulty_breakdown | false | present |
| memory_contamination | memory contamination mechanism | protocol-fixture | paired_bootstrap_delta;BH-FDR q_value;bootstrap_ci | false | present |
| power_detectable_effect_note | statistical power and detectable effects | planning-note | paired_sign_flip_permutation_power;detectable_effect_grid | false | present |
| external_reproduction_gate | external reproduction intake and environment coverage | threshold-gate | environment_coverage_gate;independent_report_count_gate | false | present |

## Protocol Coverage

| Required artifact | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| direct-provider manifest schema or contract | covered-by-fixture | direct_api_pilot | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| raw seed rows | covered-by-fixture | direct_api_pilot;execution_ladder;memory_contamination | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| aggregate rows | covered-by-fixture | execution_ladder;memory_contamination | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| significance table | covered-by-fixture | memory_contamination | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| ranking-stability table | covered-by-fixture | execution_ladder | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| contamination probe report | covered-by-fixture | memory_contamination | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| execution-sensitivity report | covered-by-fixture | execution_ladder | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| FinAudit pilot report | covered-by-fixture | finaudit_pilot | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| power curve or detectable effect note | covered-by-artifact | power_detectable_effect_note | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| direct API model matrix plan | covered-by-artifact | direct_api_model_matrix_plan | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| direct API model matrix gate | covered-by-artifact | direct_api_matrix_gate | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| external reproduction report gate | covered-by-artifact | external_reproduction_gate | Public artifact coverage supports protocol plumbing and claim boundaries; scientific claims require non-fixture direct API rows and scale thresholds. |
| external reproduction bundle | open-gap | gap:external_reproduction_reports | Required by protocol but not yet satisfied by public v0.3 artifacts. |

## Open Gaps

| Gap | Required for | Missing evidence | Current status |
| --- | --- | --- | --- |
| direct_api_model_matrix | scientific model reliability claims | direct API model rows with at least 10 seeds and 3 samples per seed, or explicit pilot labeling | plan/preflight and threshold gate exist; current public rows are fixture/pilot evidence and no non-fixture direct API group has run |
| external_reproduction_reports | external reproducibility claim | three independent reproduction reports covering Windows/macOS, Linux, and Colab/Binder | v0.3 intake gate exists; no accepted independent reports are present |
