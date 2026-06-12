# Audit-Agent Pilot: deepseek-v4-pro on 100 Defect-Injected Trajectories

First model evaluation of the FinAudit task family (research plan 04).
One defect per trajectory (25 per kind); the auditor reports structured
findings scored against injected ground truth. Compact audit view,
single pass, no retries.

| Slice | Tasks | Recall | Precision |
| --- | ---: | ---: | ---: |
| ALL | 100 | 0.79 | 0.66 |
| difficulty:L1 | 25 | 0.52 | 0.39 |
| difficulty:L2 | 50 | 0.90 | 0.78 |
| difficulty:L3 | 25 | 0.84 | 0.72 |
| kind:provenance_drift | 25 | 1.00 | 1.00 |
| kind:silent_risk_edit | 25 | 0.80 | 0.61 |
| kind:tampered_fill_price | 25 | 0.84 | 0.72 |
| kind:unclipped_position | 25 | 0.52 | 0.39 |

## Headline: difficulty inversion

The nominally easiest defect (L1 `unclipped_position`: an approved weight
of 0.8 against a documented 0.35 cap, visible in a single record) has the
worst detection (recall 0.52), while cross-record consistency checks
(`provenance_drift`, recall 1.00) and recomputation checks
(`tampered_fill_price`, 0.84) score far higher. The auditor pattern-matches
inconsistencies between records but does not systematically check stated
constraints against values - the opposite of difficulty ordering assumed
in the task design, and a concrete failure mode for LLM-as-auditor
deployments.

Reproduce: `python scripts/generate_audit_tasks.py --tasks 100 --periods 20
--output-dir outputs/audit_tasks` then `python scripts/run_audit_eval.py`.
