# Poe And Direct-DeepSeek Skill-Task Experiments

The highest-value use of additional Poe tokens is not another trading-profit
leaderboard. TradeArena already has synthetic, real-market, execution-shock,
classical-baseline, and calibration snapshots. The more distinctive research
question is whether frontier models can act as financial-audit agents:

> Can an LLM reliably inspect trajectories, understand risk feedback, identify
> execution frictions, reproduce artifacts, and avoid claim overreach?

## Recommended Poe Token Run

```bash
python scripts/run_poe_skill_task_matrix.py --repeats 3
```

Default settings:

- models: `poe:gpt-5.5`, `poe:gemini-3.1-pro`, `poe:kimi-k2.5`,
  `poe:glm-5`, and `poe:claude-opus-4.7`;
- tasks: all 12 public tasks under `examples/skill_tasks/`;
- repeats: 3 answer sets per model;
- planned calls: 180;
- estimated budget: roughly 350k-400k Poe tokens, depending on provider tokenization
  and answer length.

DeepSeek is intentionally not routed through Poe. To include direct DeepSeek
rows, run:

```bash
python scripts/run_poe_skill_task_matrix.py --repeats 3 --include-deepseek
```

This appends `deepseek:deepseek-v4-flash` and `deepseek:deepseek-v4-pro`, using
`DEEPSEEK_API_KEY` and `https://api.deepseek.com`. The Poe rows still use
`POE_API_KEY` and `https://api.poe.com/v1`.

Raw provider prompts and raw model answers are written only under ignored local
outputs/cache:

- `outputs/poe_skill_task_answers/<run>/`;
- `outputs/llm_cache/poe_skill_tasks/`.

Tracked public outputs contain aggregate scores only:

- `docs/results/poe_skill_task_matrix.md`;
- `docs/results/poe_skill_task_matrix.csv`.

## Why this experiment is worth the tokens

The experiment directly supports the repo's current research positioning:

- **Audit accuracy:** does the model find risk edits, rejected orders, partial
  fills, and intent-to-execution mismatches?
- **Risk-gate understanding:** does it explain clipped/blocked decisions and
  feedback adaptation without reducing everything to return?
- **Execution-boundary awareness:** does it avoid treating stress simulation as
  calibrated transaction-cost evidence?
- **Claim discipline:** does it separate engineering, benchmark, and scientific
  claims?
- **Reproduction awareness:** does it report commit, command, hash, artifact
  path, and data-source flags?
- **Plugin engineering:** can it propose a narrow plugin plus deterministic
  tests without changing runner orchestration?

This is a cleaner ICLR-style model comparison than asking which model appears
profitable in one market window.

## Smoke run

Use one model and two tasks before spending the full budget:

```bash
python scripts/run_poe_skill_task_matrix.py \
  --models poe:gpt-5.5 \
  --limit-tasks trajectory_audit_001,execution_boundary_001 \
  --repeats 1
```

Direct DeepSeek smoke:

```bash
python scripts/run_poe_skill_task_matrix.py \
  --models deepseek:deepseek-v4-pro \
  --limit-tasks trajectory_audit_001,execution_boundary_001 \
  --repeats 1
```

## Dry run

```bash
python scripts/run_poe_skill_task_matrix.py --dry-run --repeats 3
```

The dry run writes the planned call matrix without contacting Poe or DeepSeek.
