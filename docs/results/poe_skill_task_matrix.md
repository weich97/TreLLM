# Provider Skill-Task Matrix

This report evaluates Poe-hosted models, and optionally direct DeepSeek models, as financial-audit agents rather than trading strategies.
The public artifact contains aggregate scores only; raw prompts and raw model answers stay in ignored local outputs/cache.

## Experiment Plan

- Prompt version: `poe-skill-audit-v0.1`.
- Models: `poe:gpt-5.5`, `poe:gemini-3.1-pro`, `poe:kimi-k2.5`, `poe:glm-5`, `poe:claude-opus-4.7`.
- Tasks: 12.
- Repeats: 3.
- Planned calls: 180.
- Estimated token budget: about 352,140 tokens.

## Model Aggregate

| Provider | Model | Repeats | Avg tasks passed | Avg points | Avg score | Hard fails |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `poe` | `kimi-k2.5` | 3 | 11.0/12 | 54.0/60 | 90.0% | 0 |
| `poe` | `gpt-5.5` | 3 | 9.0/12 | 46.0/60 | 76.7% | 6 |
| `poe` | `claude-opus-4.7` | 3 | 9.0/12 | 46.0/60 | 76.7% | 3 |
| `poe` | `glm-5` | 3 | 10.0/12 | 45.0/60 | 75.0% | 6 |
| `poe` | `gemini-3.1-pro` | 3 | 8.0/12 | 44.0/60 | 73.3% | 3 |

Interpretation: these are audit-skill scores, not trading-performance scores. A higher row means the model more reliably followed TradeArena's public audit, risk, execution-boundary, reproduction, claim-boundary, and plugin-review rubrics.

## Repeat-Level Scorecard

| Provider | Model | Repeat | Tasks passed | Points | Score | Hard fails |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `poe` | `gpt-5.5` | 1 | 9/12 | 46/60 | 76.7% | 2 |
| `poe` | `gpt-5.5` | 2 | 9/12 | 46/60 | 76.7% | 2 |
| `poe` | `gpt-5.5` | 3 | 9/12 | 46/60 | 76.7% | 2 |
| `poe` | `gemini-3.1-pro` | 1 | 8/12 | 44/60 | 73.3% | 1 |
| `poe` | `gemini-3.1-pro` | 2 | 8/12 | 44/60 | 73.3% | 1 |
| `poe` | `gemini-3.1-pro` | 3 | 8/12 | 44/60 | 73.3% | 1 |
| `poe` | `kimi-k2.5` | 1 | 11/12 | 54/60 | 90.0% | 0 |
| `poe` | `kimi-k2.5` | 2 | 11/12 | 54/60 | 90.0% | 0 |
| `poe` | `kimi-k2.5` | 3 | 11/12 | 54/60 | 90.0% | 0 |
| `poe` | `glm-5` | 1 | 10/12 | 45/60 | 75.0% | 2 |
| `poe` | `glm-5` | 2 | 10/12 | 45/60 | 75.0% | 2 |
| `poe` | `glm-5` | 3 | 10/12 | 45/60 | 75.0% | 2 |
| `poe` | `claude-opus-4.7` | 1 | 9/12 | 46/60 | 76.7% | 1 |
| `poe` | `claude-opus-4.7` | 2 | 9/12 | 46/60 | 76.7% | 1 |
| `poe` | `claude-opus-4.7` | 3 | 9/12 | 46/60 | 76.7% | 1 |

## Ability Breakdown

| Provider | Model | Repeat | Ability | Tasks passed | Points | Score |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `poe` | `gpt-5.5` | 1 | Audit accuracy | 1/2 | 7/10 | 70.0% |
| `poe` | `gpt-5.5` | 1 | Risk-gate understanding | 2/2 | 10/10 | 100.0% |
| `poe` | `gpt-5.5` | 1 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `gpt-5.5` | 1 | Claim discipline | 2/2 | 10/10 | 100.0% |
| `poe` | `gpt-5.5` | 1 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `gpt-5.5` | 1 | Plugin engineering | 0/2 | 0/10 | 0.0% |
| `poe` | `gpt-5.5` | 2 | Audit accuracy | 1/2 | 7/10 | 70.0% |
| `poe` | `gpt-5.5` | 2 | Risk-gate understanding | 2/2 | 10/10 | 100.0% |
| `poe` | `gpt-5.5` | 2 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `gpt-5.5` | 2 | Claim discipline | 2/2 | 10/10 | 100.0% |
| `poe` | `gpt-5.5` | 2 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `gpt-5.5` | 2 | Plugin engineering | 0/2 | 0/10 | 0.0% |
| `poe` | `gpt-5.5` | 3 | Audit accuracy | 1/2 | 7/10 | 70.0% |
| `poe` | `gpt-5.5` | 3 | Risk-gate understanding | 2/2 | 10/10 | 100.0% |
| `poe` | `gpt-5.5` | 3 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `gpt-5.5` | 3 | Claim discipline | 2/2 | 10/10 | 100.0% |
| `poe` | `gpt-5.5` | 3 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `gpt-5.5` | 3 | Plugin engineering | 0/2 | 0/10 | 0.0% |
| `poe` | `gemini-3.1-pro` | 1 | Audit accuracy | 1/2 | 6/10 | 60.0% |
| `poe` | `gemini-3.1-pro` | 1 | Risk-gate understanding | 2/2 | 9/10 | 90.0% |
| `poe` | `gemini-3.1-pro` | 1 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `gemini-3.1-pro` | 1 | Claim discipline | 1/2 | 7/10 | 70.0% |
| `poe` | `gemini-3.1-pro` | 1 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `gemini-3.1-pro` | 1 | Plugin engineering | 0/2 | 3/10 | 30.0% |
| `poe` | `gemini-3.1-pro` | 2 | Audit accuracy | 1/2 | 6/10 | 60.0% |
| `poe` | `gemini-3.1-pro` | 2 | Risk-gate understanding | 2/2 | 9/10 | 90.0% |
| `poe` | `gemini-3.1-pro` | 2 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `gemini-3.1-pro` | 2 | Claim discipline | 1/2 | 7/10 | 70.0% |
| `poe` | `gemini-3.1-pro` | 2 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `gemini-3.1-pro` | 2 | Plugin engineering | 0/2 | 3/10 | 30.0% |
| `poe` | `gemini-3.1-pro` | 3 | Audit accuracy | 1/2 | 6/10 | 60.0% |
| `poe` | `gemini-3.1-pro` | 3 | Risk-gate understanding | 2/2 | 9/10 | 90.0% |
| `poe` | `gemini-3.1-pro` | 3 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `gemini-3.1-pro` | 3 | Claim discipline | 1/2 | 7/10 | 70.0% |
| `poe` | `gemini-3.1-pro` | 3 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `gemini-3.1-pro` | 3 | Plugin engineering | 0/2 | 3/10 | 30.0% |
| `poe` | `kimi-k2.5` | 1 | Audit accuracy | 2/2 | 8/10 | 80.0% |
| `poe` | `kimi-k2.5` | 1 | Risk-gate understanding | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 1 | Execution-boundary awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 1 | Claim discipline | 1/2 | 6/10 | 60.0% |
| `poe` | `kimi-k2.5` | 1 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 1 | Plugin engineering | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 2 | Audit accuracy | 2/2 | 8/10 | 80.0% |
| `poe` | `kimi-k2.5` | 2 | Risk-gate understanding | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 2 | Execution-boundary awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 2 | Claim discipline | 1/2 | 6/10 | 60.0% |
| `poe` | `kimi-k2.5` | 2 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 2 | Plugin engineering | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 3 | Audit accuracy | 2/2 | 8/10 | 80.0% |
| `poe` | `kimi-k2.5` | 3 | Risk-gate understanding | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 3 | Execution-boundary awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 3 | Claim discipline | 1/2 | 6/10 | 60.0% |
| `poe` | `kimi-k2.5` | 3 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `kimi-k2.5` | 3 | Plugin engineering | 2/2 | 10/10 | 100.0% |
| `poe` | `glm-5` | 1 | Audit accuracy | 2/2 | 8/10 | 80.0% |
| `poe` | `glm-5` | 1 | Risk-gate understanding | 1/2 | 4/10 | 40.0% |
| `poe` | `glm-5` | 1 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `glm-5` | 1 | Claim discipline | 2/2 | 9/10 | 90.0% |
| `poe` | `glm-5` | 1 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `glm-5` | 1 | Plugin engineering | 1/2 | 5/10 | 50.0% |
| `poe` | `glm-5` | 2 | Audit accuracy | 2/2 | 8/10 | 80.0% |
| `poe` | `glm-5` | 2 | Risk-gate understanding | 1/2 | 4/10 | 40.0% |
| `poe` | `glm-5` | 2 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `glm-5` | 2 | Claim discipline | 2/2 | 9/10 | 90.0% |
| `poe` | `glm-5` | 2 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `glm-5` | 2 | Plugin engineering | 1/2 | 5/10 | 50.0% |
| `poe` | `glm-5` | 3 | Audit accuracy | 2/2 | 8/10 | 80.0% |
| `poe` | `glm-5` | 3 | Risk-gate understanding | 1/2 | 4/10 | 40.0% |
| `poe` | `glm-5` | 3 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `glm-5` | 3 | Claim discipline | 2/2 | 9/10 | 90.0% |
| `poe` | `glm-5` | 3 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `glm-5` | 3 | Plugin engineering | 1/2 | 5/10 | 50.0% |
| `poe` | `claude-opus-4.7` | 1 | Audit accuracy | 1/2 | 6/10 | 60.0% |
| `poe` | `claude-opus-4.7` | 1 | Risk-gate understanding | 2/2 | 9/10 | 90.0% |
| `poe` | `claude-opus-4.7` | 1 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `claude-opus-4.7` | 1 | Claim discipline | 1/2 | 7/10 | 70.0% |
| `poe` | `claude-opus-4.7` | 1 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `claude-opus-4.7` | 1 | Plugin engineering | 1/2 | 5/10 | 50.0% |
| `poe` | `claude-opus-4.7` | 2 | Audit accuracy | 1/2 | 6/10 | 60.0% |
| `poe` | `claude-opus-4.7` | 2 | Risk-gate understanding | 2/2 | 9/10 | 90.0% |
| `poe` | `claude-opus-4.7` | 2 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `claude-opus-4.7` | 2 | Claim discipline | 1/2 | 7/10 | 70.0% |
| `poe` | `claude-opus-4.7` | 2 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `claude-opus-4.7` | 2 | Plugin engineering | 1/2 | 5/10 | 50.0% |
| `poe` | `claude-opus-4.7` | 3 | Audit accuracy | 1/2 | 6/10 | 60.0% |
| `poe` | `claude-opus-4.7` | 3 | Risk-gate understanding | 2/2 | 9/10 | 90.0% |
| `poe` | `claude-opus-4.7` | 3 | Execution-boundary awareness | 2/2 | 9/10 | 90.0% |
| `poe` | `claude-opus-4.7` | 3 | Claim discipline | 1/2 | 7/10 | 70.0% |
| `poe` | `claude-opus-4.7` | 3 | Reproduction awareness | 2/2 | 10/10 | 100.0% |
| `poe` | `claude-opus-4.7` | 3 | Plugin engineering | 1/2 | 5/10 | 50.0% |

## Reproduction

```bash
python scripts/run_poe_skill_task_matrix.py --repeats 3
python scripts/run_poe_skill_task_matrix.py --repeats 3 --include-deepseek
python scripts/score_skill_task.py --tasks-dir examples/skill_tasks --answers-dir outputs/poe_skill_task_answers/<run>/<model_repeat>
```
