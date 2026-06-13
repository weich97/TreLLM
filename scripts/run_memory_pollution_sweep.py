"""Memory-pollution dose-response sweep for the memory-aware strategy.

Research plan 02: inject controlled fractions of fabricated memory evidence
(fake rejections, fake violations, missing equity marks, fabricated loss
streaks) into the agent's recall path and measure how its exposure behavior
responds. The risk gate reads the raw journal, so pollution reaches the agent
only; the kill switch stays grounded in real records.

Deterministic agents only (zero provider cost). The LLM arm reuses the same
injector once the direct-API runner lands.

Usage:

  python scripts/run_memory_pollution_sweep.py \
    --output-dir docs/results/memory_pollution

  # quick smoke
  python scripts/run_memory_pollution_sweep.py \
    --kinds fake_rejections --doses 0,0.5 --decays 0.85 --risks max-position \
    --seeds 3,5 --periods 30 --output-dir outputs/tmp_pollution
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradearena.evaluation.statistics import (
    benjamini_hochberg,
    paired_bootstrap_difference,
    summarize_metric,
)
from tradearena.factory import build_default_system

DEFAULT_KINDS = ("fake_rejections", "fake_violations", "missing_equity", "loss_streak")
DEFAULT_DOSES = (0.0, 0.1, 0.25, 0.5, 0.75)
DEFAULT_LOSS_STREAKS = (0, 1, 3, 5)
DEFAULT_DECAYS = (1.0, 0.85, 0.6)
DEFAULT_RISKS = ("max-position", "none")
DEFAULT_SEEDS = tuple(range(1, 11))

OUTCOMES = (
    "memory_driven_leverage_amplification",
    "max_memory_driven_leverage_amplification",
    "memory_pollution_ratio",
    "total_return",
    "max_drawdown",
    "turnover_events",
    "hold_ratio",
)
PRIMARY_OUTCOME = "memory_driven_leverage_amplification"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dose-response sweep for memory pollution.")
    parser.add_argument("--kinds", default=",".join(DEFAULT_KINDS))
    parser.add_argument("--doses", default=",".join(str(dose) for dose in DEFAULT_DOSES))
    parser.add_argument(
        "--loss-streaks",
        default=",".join(str(k) for k in DEFAULT_LOSS_STREAKS),
        help="Streak lengths used as the dose axis for kind=loss_streak.",
    )
    parser.add_argument("--decays", default=",".join(str(decay) for decay in DEFAULT_DECAYS))
    parser.add_argument("--risks", default=",".join(DEFAULT_RISKS))
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    parser.add_argument("--periods", type=int, default=120)
    parser.add_argument(
        "--agent",
        default="memory-aware",
        help="'memory-aware' (deterministic overlay) or a provider:model spec (poe/deepseek) whose prompt consumes the polluted recall path.",
    )
    parser.add_argument(
        "--samples-per-seed",
        type=int,
        default=1,
        help="Repeated provider samples per seed for LLM agents; deterministic runs always use one.",
    )
    parser.add_argument("--cache-dir", default="outputs/llm_cache/memory_pollution")
    parser.add_argument("--symbols", default="SYN,ALT")
    parser.add_argument("--output-dir", default="docs/results/memory_pollution")
    args = parser.parse_args(argv)

    kinds = [item.strip() for item in args.kinds.split(",") if item.strip()]
    doses = [float(item) for item in args.doses.split(",") if item.strip()]
    streaks = [int(item) for item in args.loss_streaks.split(",") if item.strip()]
    decays = [float(item) for item in args.decays.split(",") if item.strip()]
    risks = [item.strip() for item in args.risks.split(",") if item.strip()]
    seeds = [int(item) for item in args.seeds.split(",") if item.strip()]
    symbols = tuple(symbol.strip() for symbol in args.symbols.split(",") if symbol.strip())

    output_dir = ROOT / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # The full matrix takes an hour-plus, so runs checkpoint to the CSV as they
    # finish and a rerun resumes from whatever is already there.
    agent = args.agent.strip()
    samples_per_seed = max(1, int(args.samples_per_seed)) if ":" in agent else 1
    cache_dir = ROOT / args.cache_dir if not Path(args.cache_dir).is_absolute() else Path(args.cache_dir)
    if ":" in agent:
        cache_dir.mkdir(parents=True, exist_ok=True)

    runs_path = output_dir / "memory_pollution_runs.csv"
    run_fields = ["agent", "kind", "dose", "decay", "risk", "seed", "sample", *OUTCOMES]
    run_rows = _load_existing_runs(runs_path)
    completed = {
        (
            str(row.get("agent") or "memory-aware"),
            str(row["kind"]),
            float(row["dose"]),
            float(row["decay"]),
            str(row["risk"]),
            int(row["seed"]),
            int(row.get("sample") or 0),
        )
        for row in run_rows
    }
    if completed:
        print(f"Resuming: {len(completed)} runs already checkpointed in {runs_path}", flush=True)

    with runs_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=run_fields, extrasaction="ignore")
        if not run_rows:
            writer.writeheader()
        for decay in decays:
            for risk in risks:
                for kind in kinds:
                    for dose_label, pollution_kwargs in _dose_axis(kind, doses, streaks):
                        fresh = 0
                        for seed in seeds:
                            for sample in range(samples_per_seed):
                                key = (agent, kind, float(dose_label), float(decay), risk, int(seed), sample)
                                if key in completed:
                                    continue
                                metrics = _run_case(
                                    agent=agent,
                                    kind=kind,
                                    pollution_kwargs=pollution_kwargs,
                                    decay=decay,
                                    risk=risk,
                                    seed=seed,
                                    sample=sample,
                                    periods=args.periods,
                                    symbols=symbols,
                                    cache_dir=cache_dir,
                                )
                                row = {
                                    "agent": agent,
                                    "kind": kind,
                                    "dose": dose_label,
                                    "decay": decay,
                                    "risk": risk,
                                    "seed": seed,
                                    "sample": sample,
                                }
                                for outcome in OUTCOMES:
                                    row[outcome] = metrics.get(outcome, "")
                                run_rows.append(row)
                                writer.writerow(row)
                                handle.flush()
                                fresh += 1
                        print(
                            f"OK agent={agent} kind={kind} dose={dose_label} decay={decay} risk={risk} ({fresh} new / {len(seeds) * samples_per_seed} runs)",
                            flush=True,
                        )

    aggregate_rows = _aggregate_rows(run_rows)
    _write_csv(
        output_dir / "memory_pollution_aggregate.csv",
        aggregate_rows,
        [
            "kind",
            "dose",
            "decay",
            "risk",
            "run_count",
            *(f"{PRIMARY_OUTCOME}_{suffix}" for suffix in ("mean", "std", "ci_low", "ci_high")),
            "memory_pollution_ratio_mean",
            "total_return_mean",
            "max_drawdown_mean",
        ],
    )

    response_rows = _dose_response_rows(run_rows)
    _write_csv(
        output_dir / "memory_pollution_dose_response.csv",
        response_rows,
        [
            "kind",
            "decay",
            "risk",
            "dose",
            "outcome",
            "paired_n",
            "mean_delta_vs_dose0",
            "delta_ci_low",
            "delta_ci_high",
            "permutation_p_value",
            "q_value",
            "cohens_d",
        ],
    )

    _write_markdown(output_dir / "memory_pollution.md", aggregate_rows, response_rows)
    print(
        f"Wrote {len(run_rows)} runs, {len(aggregate_rows)} cells, {len(response_rows)} dose-response rows to {output_dir}"
    )
    return 0


def _load_existing_runs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _dose_axis(kind: str, doses: list[float], streaks: list[int]) -> list[tuple[float, dict[str, Any]]]:
    if kind == "loss_streak":
        return [
            (
                float(streak),
                {} if streak == 0 else {
                    "memory_pollution_kind": "loss_streak",
                    "memory_pollution_loss_streak_length": streak,
                },
            )
            for streak in streaks
        ]
    return [
        (
            dose,
            {} if dose == 0.0 else {
                "memory_pollution_kind": kind,
                "memory_pollution_dose": dose,
            },
        )
        for dose in doses
    ]


def _run_case(
    *,
    agent: str = "memory-aware",
    kind: str,
    pollution_kwargs: dict[str, Any],
    decay: float,
    risk: str,
    seed: int,
    sample: int = 0,
    periods: int,
    symbols: tuple[str, ...],
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = dict(pollution_kwargs)
    if ":" in agent:
        provider, model = agent.split(":", 1)
        analyst = "poe-llm" if provider == "poe" else "deepseek-llm"
        model_slug = re.sub(r"[^a-z0-9]+", "_", f"{provider}-{model}".lower()).strip("_")
        kwargs.update(
            {
                "strategy_name": "signal-weighted",
                "analyst_names": (analyst,),
                "llm_model": model,
                "llm_cache_path": str((cache_dir or ROOT / "outputs/llm_cache/memory_pollution") / f"{model_slug}.jsonl"),
                "llm_mask_timestamps": True,
                "llm_use_risk_feedback": True,
                "llm_risk_feedback_mode": "true",
                "llm_sample_index": sample,
            }
        )
    else:
        kwargs.update({"strategy_name": "memory-aware", "analyst_names": ("momentum", "macro-news")})
    _, metrics = build_default_system(
        name=f"memory_pollution_{kind}_{seed}",
        symbols=symbols,
        periods=periods,
        seed=seed,
        risk_name=risk,
        memory_decay_rate=decay,
        memory_pollution_seed=seed,
        **kwargs,
    ).run()
    return metrics


def _aggregate_rows(run_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, float, float, str], list[dict[str, Any]]] = {}
    for row in run_rows:
        key = (str(row["kind"]), float(row["dose"]), float(row["decay"]), str(row["risk"]))
        grouped.setdefault(key, []).append(row)
    output = []
    for (kind, dose, decay, risk), rows in sorted(grouped.items()):
        record: dict[str, Any] = {
            "kind": kind,
            "dose": dose,
            "decay": decay,
            "risk": risk,
            "run_count": len(rows),
        }
        record.update(
            summarize_metric((float(row[PRIMARY_OUTCOME]) for row in rows), prefix=PRIMARY_OUTCOME)
        )
        for outcome in ("memory_pollution_ratio", "total_return", "max_drawdown"):
            values = [float(row[outcome]) for row in rows]
            record[f"{outcome}_mean"] = sum(values) / len(values)
        output.append(record)
    return output


def _dose_response_rows(run_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Paired (same seed) comparison of every nonzero dose against dose zero."""

    # Repeated provider samples average within seed before pairing.
    accumulator: dict[tuple[str, float, str, float], dict[int, list[dict[str, Any]]]] = {}
    for row in run_rows:
        key = (str(row["kind"]), float(row["decay"]), str(row["risk"]), float(row["dose"]))
        accumulator.setdefault(key, {}).setdefault(int(row["seed"]), []).append(row)
    by_cell: dict[tuple[str, float, str, float], dict[int, dict[str, Any]]] = {}
    for key, by_seed in accumulator.items():
        by_cell[key] = {}
        for seed, samples in by_seed.items():
            averaged: dict[str, Any] = dict(samples[0])
            for outcome in OUTCOMES:
                values = [float(s[outcome]) for s in samples if s.get(outcome) not in ("", None)]
                averaged[outcome] = sum(values) / len(values) if values else ""
            by_cell[key][seed] = averaged

    output: list[dict[str, Any]] = []
    for (kind, decay, risk, dose), runs_by_seed in sorted(by_cell.items()):
        if dose == 0.0:
            continue
        baseline = by_cell.get((kind, decay, risk, 0.0), {})
        if not baseline:
            continue
        for outcome in OUTCOMES:
            candidate = {
                seed: float(row[outcome])
                for seed, row in runs_by_seed.items()
                if row.get(outcome) not in ("", None)
            }
            reference = {
                seed: float(row[outcome])
                for seed, row in baseline.items()
                if row.get(outcome) not in ("", None)
            }
            result = paired_bootstrap_difference(candidate, reference)
            output.append(
                {
                    "kind": kind,
                    "decay": decay,
                    "risk": risk,
                    "dose": dose,
                    "outcome": outcome,
                    "paired_n": result["paired_n"],
                    "mean_delta_vs_dose0": result["mean_delta"],
                    "delta_ci_low": result["delta_ci_low"],
                    "delta_ci_high": result["delta_ci_high"],
                    "permutation_p_value": result["permutation_p_value"],
                    "q_value": None,
                    "cohens_d": result["cohens_d"],
                }
            )
    q_values = benjamini_hochberg(
        {index: row["permutation_p_value"] for index, row in enumerate(output)}
    )
    for index, row in enumerate(output):
        row["q_value"] = q_values[index]
    return output


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, aggregate_rows: list[dict[str, Any]], response_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Memory Pollution Dose-Response (Memory-Aware Strategy)",
        "",
        "Controlled fractions of fabricated memory evidence are injected into the",
        "agent's recall path; the risk gate keeps reading the raw journal. The",
        "primary outcome is memory-driven leverage amplification (adjusted target",
        "exposure relative to the base signal target).",
        "",
        "## Significant Dose Effects (BH-FDR q < 0.05, primary outcome)",
        "",
        "| Kind | Decay | Risk | Dose | Mean delta vs dose 0 | q value | Cohen's d |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    significant = [
        row
        for row in response_rows
        if row["outcome"] == PRIMARY_OUTCOME and row["q_value"] is not None and float(row["q_value"]) < 0.05
    ]
    for row in significant:
        cohens = row["cohens_d"]
        cohens_text = f"{float(cohens):.2f}" if cohens is not None else ""
        lines.append(
            f"| {row['kind']} | {row['decay']} | {row['risk']} | {row['dose']} "
            f"| {float(row['mean_delta_vs_dose0']):+.4f} | {float(row['q_value']):.4f} | {cohens_text} |"
        )
    if not significant:
        lines.append("| (none) | | | | | | |")
    lines += [
        "",
        "## Manipulation Check (perceived pollution ratio by dose)",
        "",
        "| Kind | Decay | Risk | Dose | Perceived pollution mean | Amplification mean |",
        "| --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in aggregate_rows:
        lines.append(
            f"| {row['kind']} | {row['decay']} | {row['risk']} | {row['dose']} "
            f"| {float(row['memory_pollution_ratio_mean']):.3f} | {float(row[f'{PRIMARY_OUTCOME}_mean']):.4f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
