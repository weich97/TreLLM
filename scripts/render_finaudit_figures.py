"""Render the FinAudit paper figures from the released audit-eval summary.

Figure 1: grouped bars of recall by difficulty tier (L1/L2/L3) per auditor,
ordered by overall recall, making the weak-auditor L1 collapse visible.
Figure 2: heatmap of recall by defect family per auditor, separating
constraint-check families (uncapped, silent edit) from inconsistency
families (provenance, tampered fill).

Usage:
  python scripts/render_finaudit_figures.py \
    --summary docs/results/audit_eval_pilot/audit_eval_summary.csv \
    --output-dir paper/finaudit/figures
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

LABEL = {
    "poe:gpt-5.5": "gpt-5.5",
    "poe:claude-opus-4.7": "claude-opus-4.7",
    "poe:gemini-3.1-pro": "gemini-3.1-pro",
    "deepseek:deepseek-v4-pro": "deepseek-v4-pro$^\\dagger$",
    "glm:glm-5": "glm-5$^\\dagger$",
    "poe:glm-5": "glm-5 (routed)",
}
DIFF = [("difficulty:L1", "L1 single-record"), ("difficulty:L2", "L2 cross-record"), ("difficulty:L3", "L3 recompute")]
KINDS = [
    ("kind:unclipped_position", "uncapped"),
    ("kind:silent_risk_edit", "silent edit"),
    ("kind:provenance_drift", "provenance"),
    ("kind:tampered_fill_price", "tampered fill"),
]


def _load(summary: Path) -> dict[str, dict[str, float]]:
    table: dict[str, dict[str, float]] = defaultdict(dict)
    with summary.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            table[row["model"]][row["slice"]] = float(row["recall"])
    return table


def _ordered_models(table: dict[str, dict[str, float]]) -> list[str]:
    return sorted((m for m in table if m in LABEL), key=lambda m: -table[m].get("ALL", 0.0))


def render_difficulty_bars(table: dict[str, dict[str, float]], output_dir: Path) -> Path:
    models = _ordered_models(table)
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    width = 0.26
    colors = ["#c44e52", "#55a868", "#4c72b0"]
    for j, (slice_key, label) in enumerate(DIFF):
        xs = [i + (j - 1) * width for i in range(len(models))]
        ax.bar(xs, [table[m].get(slice_key, 0.0) for m in models], width, label=label, color=colors[j])
    ax.set_xticks(range(len(models)), [LABEL[m] for m in models], rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Recall", fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color="gray", linewidth=0.5, linestyle=":")
    ax.legend(fontsize=8, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    path = output_dir / "recall_by_difficulty.pdf"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def render_kind_heatmap(table: dict[str, dict[str, float]], output_dir: Path) -> Path:
    models = _ordered_models(table)
    grid = [[table[m].get(k, 0.0) for k, _ in KINDS] for m in models]
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    image = ax.imshow(grid, cmap="RdYlGn", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(KINDS)), [lbl for _, lbl in KINDS], fontsize=8)
    ax.set_yticks(range(len(models)), [LABEL[m] for m in models], fontsize=8)
    for i in range(len(models)):
        for j in range(len(KINDS)):
            ax.text(j, i, f"{grid[i][j]:.2f}", ha="center", va="center", fontsize=8)
    # Divider between constraint-check families (cols 0-1) and inconsistency (2-3).
    ax.axvline(1.5, color="black", linewidth=1.2)
    ax.set_title("constraint check $|$ inconsistency", fontsize=8)
    fig.colorbar(image, ax=ax, fraction=0.045, pad=0.03)
    fig.tight_layout()
    path = output_dir / "recall_by_kind.pdf"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render FinAudit paper figures.")
    parser.add_argument("--summary", default="docs/results/audit_eval_pilot/audit_eval_summary.csv")
    parser.add_argument("--output-dir", default="paper/finaudit/figures")
    args = parser.parse_args(argv)
    summary = ROOT / args.summary if not Path(args.summary).is_absolute() else Path(args.summary)
    output_dir = ROOT / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    table = _load(summary)
    print("wrote", render_difficulty_bars(table, output_dir))
    print("wrote", render_kind_heatmap(table, output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
