# TreLLM v0.3 Evidence Index

This index maps generated public artifacts to the v0.3 ICLR protocol claims.
It is deliberately conservative: fixture and pilot artifacts do not support headline scientific model-performance claims.

- Protocol: `trellm-v0.3-iclr-protocol`
- Present artifacts: `5 / 5`
- Fixture-covered protocol artifacts: `9 / 10`
- Open gaps: `2`
- Headline scientific claim ready: `False`
- Claim boundary: This index maps public v0.3 artifacts to protocol claims. Current artifacts validate protocol plumbing and pilot mechanisms; they do not yet support headline scientific model-performance claims.

## Artifact Map

| Artifact | Claim area | Stage | Methods | Supports headline claim | Status |
| --- | --- | --- | --- | --- | --- |
| direct_api_pilot | direct API provenance | protocol-fixture | seed/sample manifest coverage | false | present |
| execution_ladder | execution assumption sensitivity | protocol-fixture | kendall_tau;top_k_jaccard;bootstrap_ci | false | present |
| finaudit_pilot | financial trace audit | protocol-fixture | precision;recall;f1;wilson_interval;difficulty_breakdown | false | present |
| memory_contamination | memory contamination mechanism | protocol-fixture | paired_bootstrap_delta;BH-FDR q_value;bootstrap_ci | false | present |
| power_detectable_effect_note | statistical power and detectable effects | planning-note | paired_sign_flip_permutation_power;detectable_effect_grid | false | present |

## Protocol Coverage

| Required artifact | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| direct-provider manifest schema or contract | covered-by-fixture | direct_api_pilot | Fixture coverage supports protocol plumbing; scientific claims require direct API and scale thresholds. |
| raw seed rows | covered-by-fixture | direct_api_pilot;execution_ladder;memory_contamination | Fixture coverage supports protocol plumbing; scientific claims require direct API and scale thresholds. |
| aggregate rows | covered-by-fixture | execution_ladder;memory_contamination | Fixture coverage supports protocol plumbing; scientific claims require direct API and scale thresholds. |
| significance table | covered-by-fixture | memory_contamination | Fixture coverage supports protocol plumbing; scientific claims require direct API and scale thresholds. |
| ranking-stability table | covered-by-fixture | execution_ladder | Fixture coverage supports protocol plumbing; scientific claims require direct API and scale thresholds. |
| contamination probe report | covered-by-fixture | memory_contamination | Fixture coverage supports protocol plumbing; scientific claims require direct API and scale thresholds. |
| execution-sensitivity report | covered-by-fixture | execution_ladder | Fixture coverage supports protocol plumbing; scientific claims require direct API and scale thresholds. |
| FinAudit pilot report | covered-by-fixture | finaudit_pilot | Fixture coverage supports protocol plumbing; scientific claims require direct API and scale thresholds. |
| power curve or detectable effect note | covered-by-fixture | power_detectable_effect_note | Fixture coverage supports protocol plumbing; scientific claims require direct API and scale thresholds. |
| external reproduction bundle | open-gap | gap:external_reproduction_reports | Required by protocol but not yet satisfied by public v0.3 artifacts. |

## Open Gaps

| Gap | Required for | Missing evidence | Current status |
| --- | --- | --- | --- |
| direct_api_model_matrix | scientific model reliability claims | direct API model rows with at least 10 seeds and 3 samples per seed, or explicit pilot labeling | fixture-only direct API plumbing exists |
| external_reproduction_reports | external reproducibility claim | three independent reproduction reports covering Windows/macOS, Linux, and Colab/Binder | fresh-environment CI and v0.2 reproduction pack exist; independent v0.3 reports are not present |
