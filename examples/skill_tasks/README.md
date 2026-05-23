# TradeArena Skill Task Suite

This directory contains small, deterministic tasks for evaluating whether a
human reviewer or coding agent can use TradeArena skills without turning them
into trading prompts.

Each task includes:

- `input.md`: the instruction shown to the reviewer or model;
- one small artifact or expected-output note when useful;
- `rubric.json`: machine-readable grading criteria.

These tasks evaluate audit, reproduction, calibration, claim-boundary, and
plugin-authoring ability. They do not evaluate trading profitability.

## Capability Metrics

| Ability | Measurable task | Scoring |
| --- | --- | --- |
| Audit accuracy | Find risk edits, rejected orders, and partial fills in a trajectory | Rubric match against expected audit fields |
| Risk-gate understanding | Check whether a risk report is complete or misses controls | Checklist score |
| Execution-boundary awareness | Avoid describing a stress simulator as real transaction-cost evidence | Hard fail on boundary overclaim |
| Claim discipline | Classify engineering, benchmark, and scientific claims | Label accuracy |
| Reproduction awareness | Report commit, hash, command, artifact path, and data-source flags | Field coverage |
| Plugin engineering | Propose a narrow plugin with deterministic tests | Test/review checklist |

Validate the rubric suite:

```bash
python scripts/score_skill_task.py --tasks-dir examples/skill_tasks --validate-only
```

Score one answer:

```bash
python scripts/score_skill_task.py examples/skill_tasks/trajectory_audit_001 --answer answer.md
```
