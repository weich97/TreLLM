# TradeArena v0.1 Benchmark Card

TradeArena is a benchmark and audit framework, not a profitability claim. This page
gives a compact, citable snapshot of what the v0.1 artifacts show under execution
realism, risk gates, and replayable trajectories.

## One-Sentence Finding

Execution realism and risk gates materially change LLM trading-agent evaluation:
intended allocations can look very different after slippage, latency, liquidity limits,
partial fills, rejected orders, and pre-trade risk edits.

## Result Provenance

- Release: v0.1.0.
- Release commit: `4238a9b`.
- Benchmark card source: tracked snapshots under `docs/results/`.
- Reproduction command:

  ```bash
  python -m pip install -e ".[dev]"
  python scripts/run_showcase.py
  python scripts/build_benchmark_page.py
  ```

- Data: tracked synthetic, timestamp-masked, and redacted artifacts.
- Live model calls: not required for first-run reproduction.
- Raw prompt/response caches: not included.
- Intended use: benchmark and audit research, not trading advice.

## What Is Measured

- Return and max drawdown.
- Fill rate, rejection rate, latency, slippage, and partial fills.
- Risk edits, clipped decisions, violations, and audit completeness.
- Concentration / Herfindahl for portfolio probes.
- Calibration and representation robustness diagnostics.

## How To Reproduce

```bash
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
python scripts/build_benchmark_page.py
```

The page uses tracked CSV snapshots under `docs/results/` plus deterministic first-run
artifacts under `outputs/examples/`. Live model calls are not required for first-run
reproduction.

## First-Run Execution Benchmark

| Scenario | Agent / baseline | Return | Max drawdown | Fill rate | Rejection rate | Risk edits | Audit completeness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deterministic quickstart | buy_and_hold_realistic | 53.74% | -6.63% | 89.83% | 8.90% | 0 | 100.00% |
| deterministic quickstart | risk_aware_realistic | 35.08% | -1.26% | 90.34% | 7.95% | 124 | 100.00% |

## Key Result 1: Risk Gates Are Active, Not Cosmetic

Across the crisis and intraday rows, risk gates repeatedly edit or clip intended
allocations before execution. The benchmark therefore reports risk edits alongside
return, instead of treating risk control as a post-hoc metric.

## Crisis-Scene LLM Benchmark

The crisis snapshot aggregates timestamp-masked 2022 Tech/Rates and 2023 SVB-style
stress paths. Rows below average across the tracked model policies for each feedback
mode.

| Scenario | Agent / baseline | Return | Max drawdown | Fill rate | Rejection rate | Risk edits | Audit completeness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| svb_2023 | LLM policies (hidden feedback) | 1.23% | -1.86% | 75.59% | 24.41% | 212 | 100.00% |
| svb_2023 | LLM policies (placebo feedback) | 1.19% | -1.87% | 76.88% | 23.12% | 204 | 100.00% |
| svb_2023 | LLM policies (true feedback) | 1.08% | -1.87% | 78.16% | 21.84% | 196 | 100.00% |
| tech_rates_2022 | LLM policies (hidden feedback) | -3.27% | -4.89% | 65.93% | 34.07% | 914 | 100.00% |
| tech_rates_2022 | LLM policies (placebo feedback) | -2.57% | -4.40% | 63.10% | 36.90% | 906 | 100.00% |
| tech_rates_2022 | LLM policies (true feedback) | -3.09% | -4.81% | 64.33% | 35.67% | 778 | 100.00% |

## True-Feedback Model Rows

Model names are redacted or normalized labels for benchmark policies. Raw provider
prompts and responses are not shipped.

| Scenario | Policy label | Return | Max drawdown | Fill rate | Risk edits | Violations | Calibration |
| --- | --- | --- | --- | --- | --- | --- | --- |
| svb_2023 | frontier-policy-D (redacted) | 1.03% | -1.87% | 80.16% | 177 | 13 | 0.198 |
| svb_2023 | frontier-policy-B (redacted) | 1.24% | -1.89% | 77.37% | 206 | 14 | 0.207 |
| svb_2023 | frontier-policy-C (redacted) | 0.67% | -1.88% | 78.52% | 196 | 14 | 0.397 |
| svb_2023 | frontier-policy-A (redacted) | 1.39% | -1.86% | 76.60% | 203 | 14 | 0.224 |
| tech_rates_2022 | frontier-policy-D (redacted) | -1.84% | -4.79% | 62.62% | 863 | 39 | 0.071 |
| tech_rates_2022 | frontier-policy-B (redacted) | -2.49% | -4.53% | 63.90% | 969 | 41 | 0.067 |
| tech_rates_2022 | frontier-policy-C (redacted) | -5.32% | -5.32% | 69.10% | 402 | 226 | 0.435 |
| tech_rates_2022 | frontier-policy-A (redacted) | -2.72% | -4.61% | 61.69% | 880 | 38 | 0.090 |

## Key Result 2: Execution Assumptions Change Realized Exposure

The 51-stock hourly probe shows that low-liquidity and latency stress rows do not behave
like ideal fills. Fill rate, rejected orders, and realized exposure become part of the
benchmark outcome.

## 51-Stock Intraday Portfolio Probe

The intraday snapshot compares passive, deterministic, Markowitz/MVO, execution-stress,
and redacted LLM policy rows on the same 51-stock hourly panel.

| Agent / baseline | Return | Max drawdown | Fill rate | Rejected | Risk edits | Herfindahl | Audit completeness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Buy and Hold | 0.71% | -0.79% | 87.16% | 98 | 2040 | 0.019 | 100.00% |
| Deterministic Risk-Aware | -1.35% | -3.11% | 76.26% | 91 | 672 | 0.062 | 100.00% |
| Markowitz MVO | -0.54% | -1.35% | 87.94% | 185 | 357 | 0.023 | 100.00% |
| Low-Liquidity Stress | -2.16% | -3.60% | 75.55% | 95 | 672 | 0.062 | 100.00% |
| Latency Stress | 1.96% | -1.33% | 44.40% | 209 | 672 | 0.081 | 100.00% |
| Frontier Policy A (redacted) | -2.23% | -2.93% | 71.86% | 378 | 2924 | 0.045 | 100.00% |
| Frontier Policy C (redacted) | -0.53% | -2.31% | 63.60% | 254 | 1200 | 0.035 | 100.00% |

## Key Result 3: Audit Completeness Is A Benchmark Dimension

Every result row should be traceable to a trajectory rather than only to a return curve.
TradeArena therefore reports audit completeness and keeps compact, redacted result
manifests.

## Representation Robustness Snapshot

A result is more useful when the diagnostic survives multiple representation views. The
v0.1 tracked snapshot includes 80 rolling failure anchors and 320 pre-failure steps
across eight LLM trajectories.

| Embedding | View | Anchors | Pre-failure steps | Mean rank delta | Contraction rate | Mean pre-shift |
| --- | --- | --- | --- | --- | --- | --- |
| hash64 | fused | 80 | 320 | 0.471 | 67.50% | 0.071 |
| lsa32 | fused | 80 | 320 | 5.123 | 86.25% | 0.084 |
| hash64 | plan | 80 | 320 | 8.703 | 97.50% | 0.122 |
| lsa32 | plan | 80 | 320 | 4.870 | 85.00% | 0.097 |

## Limitations

- This is a benchmark and audit artifact, not financial advice.
- It is not a live-trading system and does not promise profitability.
- First-run reproduction uses tracked artifacts, not live provider calls.
- Public rows use redacted or normalized policy labels.
- Raw provider prompts, responses, credentials, and caches are not shipped.
