# TradeArena v0.1 Benchmark Snapshot

TradeArena is a benchmark and audit framework, not a profitability claim. This page gives a compact, citable snapshot of what the v0.1 artifacts show under execution realism, risk gates, and replayable trajectories.

**Core claim:** LLM trading agents can look materially different once their intended allocations pass through risk gates, slippage, latency, liquidity limits, partial fills, and rejected orders.

## How To Reproduce

```bash
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
python scripts/build_benchmark_page.py
```

The page uses tracked CSV snapshots under `docs/results/` plus deterministic first-run artifacts under `outputs/examples/`. It does not ship raw provider prompts or responses.

## First-Run Execution Benchmark

| Scenario | Agent / baseline | Return | Max drawdown | Fill rate | Rejection rate | Risk edits | Audit completeness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic quickstart | buy_and_hold_realistic | 53.74% | -6.63% | 89.83% | 8.90% | 0 | 100.00% |
| deterministic quickstart | risk_aware_realistic | 35.08% | -1.26% | 90.34% | 7.95% | 124 | 100.00% |

## Crisis-Scene LLM Benchmark

The crisis snapshot aggregates timestamp-masked 2022 Tech/Rates and 2023 SVB-style stress paths. Rows below average across the tracked model policies for each feedback mode.

| Scenario | Agent / baseline | Return | Max drawdown | Fill rate | Rejection rate | Risk edits | Audit completeness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| svb_2023 | LLM policies (hidden feedback) | 1.23% | -1.86% | 75.59% | 24.41% | 212 | 100.00% |
| svb_2023 | LLM policies (placebo feedback) | 1.19% | -1.87% | 76.88% | 23.12% | 204 | 100.00% |
| svb_2023 | LLM policies (true feedback) | 1.08% | -1.87% | 78.16% | 21.84% | 196 | 100.00% |
| tech_rates_2022 | LLM policies (hidden feedback) | -3.27% | -4.89% | 65.93% | 34.07% | 914 | 100.00% |
| tech_rates_2022 | LLM policies (placebo feedback) | -2.57% | -4.40% | 63.10% | 36.90% | 906 | 100.00% |
| tech_rates_2022 | LLM policies (true feedback) | -3.09% | -4.81% | 64.33% | 35.67% | 778 | 100.00% |

## True-Feedback Model Rows

| Scenario | Model | Return | Max drawdown | Fill rate | Risk edits | Violations | Calibration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| svb_2023 | deepseek-v4-pro | 1.03% | -1.87% | 80.16% | 177 | 13 | 0.198 |
| svb_2023 | claude-opus-4.7 | 1.24% | -1.89% | 77.37% | 206 | 14 | 0.207 |
| svb_2023 | gemini-3.1-pro | 0.67% | -1.88% | 78.52% | 196 | 14 | 0.397 |
| svb_2023 | gpt-5.5 | 1.39% | -1.86% | 76.60% | 203 | 14 | 0.224 |
| tech_rates_2022 | deepseek-v4-pro | -1.84% | -4.79% | 62.62% | 863 | 39 | 0.071 |
| tech_rates_2022 | claude-opus-4.7 | -2.49% | -4.53% | 63.90% | 969 | 41 | 0.067 |
| tech_rates_2022 | gemini-3.1-pro | -5.32% | -5.32% | 69.10% | 402 | 226 | 0.435 |
| tech_rates_2022 | gpt-5.5 | -2.72% | -4.61% | 61.69% | 880 | 38 | 0.090 |

## 51-Stock Intraday Portfolio Probe

The intraday snapshot compares passive, deterministic, Markowitz/MVO, execution-stress, and LLM policies on the same 51-stock hourly panel.

| Agent / baseline | Return | Max drawdown | Fill rate | Rejected | Risk edits | Herfindahl | Audit completeness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Buy and Hold | 0.71% | -0.79% | 87.16% | 98 | 2040 | 0.019 | 100.00% |
| Deterministic Risk-Aware | -1.35% | -3.11% | 76.26% | 91 | 672 | 0.062 | 100.00% |
| Markowitz MVO | -0.54% | -1.35% | 87.94% | 185 | 357 | 0.023 | 100.00% |
| Low-Liquidity Stress | -2.16% | -3.60% | 75.55% | 95 | 672 | 0.062 | 100.00% |
| Latency Stress | 1.96% | -1.33% | 44.40% | 209 | 672 | 0.081 | 100.00% |
| LLM GPT-5.5 | -2.23% | -2.93% | 71.86% | 378 | 2924 | 0.045 | 100.00% |
| LLM Gemini 3.1 Pro | -0.53% | -2.31% | 63.60% | 254 | 1200 | 0.035 | 100.00% |

## Representation Robustness Snapshot

A result is more useful when the diagnostic survives multiple representation views. The v0.1 tracked snapshot includes 80 rolling failure anchors and 320 pre-failure steps across eight LLM trajectories.

| Embedding | View | Anchors | Pre-failure steps | Mean rank delta | Contraction rate | Mean pre-shift |
| --- | --- | --- | --- | --- | --- | --- |
| hash64 | fused | 80 | 320 | 0.471 | 67.50% | 0.071 |
| lsa32 | fused | 80 | 320 | 5.123 | 86.25% | 0.084 |
| hash64 | plan | 80 | 320 | 8.703 | 97.50% | 0.122 |
| lsa32 | plan | 80 | 320 | 4.870 | 85.00% | 0.097 |

## Interpretation

- Risk gates are not cosmetic: they repeatedly edit intended allocations before execution.
- Execution assumptions are first-order: fill rate, rejected orders, latency, and slippage change realized exposure.
- Audit completeness is a benchmark dimension: every result row should be traceable to a trajectory, not just a return.
- These artifacts support evaluation and diagnosis. They do not provide financial advice or a live-trading guarantee.
