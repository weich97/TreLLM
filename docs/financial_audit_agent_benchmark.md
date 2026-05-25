# Financial-Audit Agent Task Suite

TradeArena skills are evaluated as audit workflows, not as trading strategies.
The central question is:

> Can an LLM or coding agent reliably audit financial decisions, understand
> risk feedback, identify execution frictions, reproduce artifacts, and avoid
> claim overreach?

This framing keeps the benchmark aligned with agent reliability and
intent-to-execution audit. A model may perform well on these tasks without
making any investment recommendation.

## What Is Scored

The task suite in `examples/skill_tasks/` contains deterministic fixtures and
rubrics. Each task points to a skill under `skills/` and asks the reviewer or
model to inspect a local artifact.

| Ability | What the task checks |
| --- | --- |
| Audit accuracy | Finds raw-intent, risk-approved, order, fill, and portfolio mismatches |
| Risk-gate understanding | Explains risk edits, warnings, blocks, and feedback adaptation |
| Execution-boundary awareness | Attributes costs without overstating stress-only evidence |
| Claim discipline | Separates engineering, benchmark, and scientific claims |
| Reproduction awareness | Reports commit, command, hash, artifact, and data-source flags |
| Plugin engineering | Keeps plugin scope narrow and adds deterministic tests |

## Why This Matters

Financial decision agents often fail before portfolio returns are visible:

- raw intent conflicts with the rationale;
- risk feedback is ignored or overfit;
- execution friction is treated as if it were calibrated fill evidence;
- cached provider rows are mistaken for model-skill claims;
- reproduction mismatches are hidden behind aggregate scores;
- plugin changes leak across data, risk, execution, and market-rule boundaries.

The skill tasks make those failures explicit and scorable.

## Evidence Boundary

Passing a skill task supports an audit-capability observation. It does not
support a profitability claim, live-trading claim, or broker-grade execution
claim. If a benchmarked model uses a skill as prompt or retrieval context, the
skill must be recorded in the run manifest so the row remains comparable.

## Commands

```bash
python scripts/validate_skill_contract.py skills
python scripts/score_skill_task.py --tasks-dir examples/skill_tasks --validate-only
python scripts/score_skill_task.py --tasks-dir examples/skill_tasks --answers-dir examples/skill_task_answers/reference
python scripts/score_skill_task_report.py --tasks-dir examples/skill_tasks --output docs/results/skill_task_matrix.md
```

The generated report is tracked at
`docs/results/skill_task_matrix.md`.

## Scoring A Model Or Reviewer

To evaluate a model, create one Markdown answer per task:

```text
examples/skill_task_answers/<answer_set>/
  manifest.json
  trajectory_audit_001.md
  intent_execution_autopsy_001.md
  ...
```

The `manifest.json` must follow
`schemas/skill_answer_set.schema.json`. It records the model/provider, prompt
version, skill version, task-input version, whether the skill files were
retrieved, and whether hidden artifacts were used. Publicly comparable
scorecards require `hidden_artifacts_used=false`.

Then run:

```bash
python scripts/score_skill_task.py \
  --tasks-dir examples/skill_tasks \
  --answers-dir examples/skill_task_answers/<answer_set>

python scripts/score_skill_task_report.py \
  --tasks-dir examples/skill_tasks \
  --answers-dir examples/skill_task_answers/<answer_set> \
  --answers-label <answer_set> \
  --output outputs/<answer_set>_skill_task_matrix.md
```

Report the model/provider, prompt version, whether skills were retrieved, and
whether the answers used hidden artifacts. Do not compare answer sets unless
they saw the same task inputs and the same skill text.
