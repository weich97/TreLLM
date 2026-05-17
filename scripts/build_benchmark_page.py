from __future__ import annotations

import argparse
import csv
import html
import json
import statistics
import textwrap
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CRISIS_CSV = ROOT / "docs/results/crisis/crisis_summary.csv"
REPRESENTATION_CSV = ROOT / "docs/results/representation/embedding_robustness.csv"
INTRADAY_CSV = ROOT / "docs/results/intraday/intraday_complex.csv"
QUICKSTART_JSON = ROOT / "outputs/examples/quickstart_core_metrics.json"
RELEASE_TAG = "v0.1.0"
RELEASE_COMMIT = "4238a9b"
POLICY_LABELS = {
    "gpt-5.5": "frontier-policy-A (redacted)",
    "claude-opus-4.7": "frontier-policy-B (redacted)",
    "gemini-3.1-pro": "frontier-policy-C (redacted)",
    "deepseek-v4-pro": "frontier-policy-D (redacted)",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the TradeArena v0.1 benchmark result page.")
    parser.add_argument("--markdown", default="docs/results/benchmark_v0_1.md")
    parser.add_argument("--html", default="outputs/examples/benchmark-v0.1.html")
    args = parser.parse_args()

    crisis_rows = _read_csv(CRISIS_CSV)
    representation_rows = _read_csv(REPRESENTATION_CSV)
    intraday_rows = _read_csv(INTRADAY_CSV) if INTRADAY_CSV.exists() else []
    quickstart_rows = _read_quickstart_rows(QUICKSTART_JSON) if QUICKSTART_JSON.exists() else []

    crisis_summary = _summarize_crisis(crisis_rows)
    crisis_true_rows = [row for row in crisis_rows if row.get("feedback") == "true"]
    representation_summary = _summarize_representation(representation_rows)

    md = _markdown(quickstart_rows, crisis_summary, crisis_true_rows, intraday_rows, representation_summary)
    html_text = _html(quickstart_rows, crisis_summary, crisis_true_rows, intraday_rows, representation_summary)

    markdown_path = ROOT / args.markdown
    html_path = ROOT / args.html
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(md, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")

    print(f"Wrote {markdown_path.relative_to(ROOT)}")
    print(f"Wrote {html_path.relative_to(ROOT)}")
    return 0


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_quickstart_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for case, metrics in sorted(data.items()):
        rows.append(
            {
                "scenario": "deterministic quickstart",
                "agent": case,
                "return": float(metrics.get("total_return", 0.0)),
                "max_drawdown": float(metrics.get("max_drawdown", 0.0)),
                "fill_rate": float(metrics.get("execution_fill_rate", metrics.get("fill_rate", 0.0))),
                "rejection_rate": _safe_ratio(float(metrics.get("rejected_order_count", 0.0)), float(metrics.get("order_count", 0.0))),
                "risk_edits": int(float(metrics.get("risk_clipped_decisions", 0.0))),
                "audit_completeness": float(metrics.get("trajectory_reproducibility_coverage", 1.0)),
            }
        )
    return rows


def _summarize_crisis(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault((row["scene"], row["feedback"]), []).append(row)

    result: list[dict[str, Any]] = []
    for (scene, feedback), group in sorted(groups.items()):
        result.append(
            {
                "scenario": scene,
                "agent": f"LLM policies ({feedback} feedback)",
                "return": _mean(group, "total_return"),
                "max_drawdown": _mean(group, "max_drawdown"),
                "fill_rate": _mean(group, "execution_fill_rate"),
                "rejection_rate": 1.0 - _mean(group, "execution_fill_rate"),
                "risk_edits": round(_mean(group, "risk_clipped_decisions")),
                "audit_completeness": 1.0,
                "calibration": _mean(group, "mean_calibration_score"),
                "models": len(group),
            }
        )
    return result


def _summarize_representation(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    keep = []
    for row in rows:
        if row.get("cohort") != "all_llm":
            continue
        if row.get("view") not in {"plan", "fused"}:
            continue
        keep.append(
            {
                "embedding": row["embedding"],
                "view": row["view"],
                "anchors": int(float(row["anchors"])),
                "pre_steps": int(float(row["pre_steps"])),
                "rank_delta": float(row["mean_effective_rank_delta"]),
                "contraction_rate": float(row["rank_contraction_rate"]),
                "mean_pre_shift": float(row["mean_pre_shift"]),
            }
        )
    return sorted(keep, key=lambda item: (item["view"], item["embedding"]))


def _markdown(
    quickstart_rows: list[dict[str, Any]],
    crisis_summary: list[dict[str, Any]],
    crisis_true_rows: list[dict[str, str]],
    intraday_rows: list[dict[str, str]],
    representation_summary: list[dict[str, Any]],
) -> str:
    provenance = _provenance_rows()
    lines = [
        "# TradeArena v0.1 Benchmark Card",
        "",
        _wrap(
            "TradeArena is a benchmark and audit framework, not a profitability "
            "claim. This page gives a compact, citable snapshot of what the "
            "v0.1 artifacts show under execution realism, risk gates, and "
            "replayable trajectories."
        ),
        "",
        "## One-Sentence Finding",
        "",
        _wrap(
            "Execution realism and risk gates materially change LLM "
            "trading-agent evaluation: intended allocations can look very "
            "different after slippage, latency, liquidity limits, partial "
            "fills, rejected orders, and pre-trade risk edits."
        ),
        "",
        "## Result Provenance",
        "",
        "- Release: v0.1.0.",
        "- Release commit: `4238a9b`.",
        "- Benchmark card source: tracked snapshots under `docs/results/`.",
        "- Reproduction command:",
        "",
        "  ```bash",
        "  python -m pip install -e \".[dev]\"",
        "  python scripts/run_showcase.py",
        "  python scripts/build_benchmark_page.py",
        "  ```",
        "",
        "- Data: tracked synthetic, timestamp-masked, and redacted artifacts.",
        "- Live model calls: not required for first-run reproduction.",
        "- Raw prompt/response caches: not included.",
        "- Intended use: benchmark and audit research, not trading advice.",
        "",
        "## What Is Measured",
        "",
        "- Return and max drawdown.",
        "- Fill rate, rejection rate, latency, slippage, and partial fills.",
        "- Risk edits, clipped decisions, violations, and audit completeness.",
        "- Concentration / Herfindahl for portfolio probes.",
        "- Calibration and representation robustness diagnostics.",
        "",
        "## How To Reproduce",
        "",
        "```bash",
        "python -m pip install -e \".[dev]\"",
        "python scripts/run_showcase.py",
        "python scripts/build_benchmark_page.py",
        "```",
        "",
        _wrap(
            "The page uses tracked CSV snapshots under `docs/results/` plus "
            "deterministic first-run artifacts under `outputs/examples/`. "
            "Live model calls are not required for first-run reproduction."
        ),
        "",
    ]

    if quickstart_rows:
        lines += [
            "## First-Run Execution Benchmark",
            "",
            _md_table(
                ["Scenario", "Agent / baseline", "Return", "Max drawdown", "Fill rate", "Rejection rate", "Risk edits", "Audit completeness"],
                [
                    [
                        row["scenario"],
                        row["agent"],
                        _pct(row["return"]),
                        _pct(row["max_drawdown"]),
                        _pct(row["fill_rate"]),
                        _pct(row["rejection_rate"]),
                        str(row["risk_edits"]),
                        _pct(row["audit_completeness"]),
                    ]
                    for row in quickstart_rows
                ],
            ),
            "",
        ]

    lines += [
        "## Key Result 1: Risk Gates Are Active, Not Cosmetic",
        "",
        _wrap(
            "Across the crisis and intraday rows, risk gates repeatedly edit "
            "or clip intended allocations before execution. The benchmark "
            "therefore reports risk edits alongside return, instead of "
            "treating risk control as a post-hoc metric."
        ),
        "",
        "## Crisis-Scene LLM Benchmark",
        "",
        _wrap(
            "The crisis snapshot aggregates timestamp-masked 2022 Tech/Rates "
            "and 2023 SVB-style stress paths. Rows below average across the "
            "tracked model policies for each feedback mode."
        ),
        "",
        _md_table(
            ["Scenario", "Agent / baseline", "Return", "Max drawdown", "Fill rate", "Rejection rate", "Risk edits", "Audit completeness"],
            [
                [
                    row["scenario"],
                    row["agent"],
                    _pct(row["return"]),
                    _pct(row["max_drawdown"]),
                    _pct(row["fill_rate"]),
                    _pct(row["rejection_rate"]),
                    str(row["risk_edits"]),
                    _pct(row["audit_completeness"]),
                ]
                for row in crisis_summary
            ],
        ),
        "",
        "## True-Feedback Model Rows",
        "",
        _wrap(
            "Model names are redacted or normalized labels for benchmark "
            "policies. Raw provider prompts and responses are not shipped."
        ),
        "",
        _md_table(
            ["Scenario", "Policy label", "Return", "Max drawdown", "Fill rate", "Risk edits", "Violations", "Calibration"],
            [
                [
                    row["scene"],
                    _policy_label(row["model"]),
                    _pct(float(row["total_return"])),
                    _pct(float(row["max_drawdown"])),
                    _pct(float(row["execution_fill_rate"])),
                    row["risk_clipped_decisions"],
                    row["risk_violation_count"],
                    f"{float(row['mean_calibration_score']):.3f}",
                ]
                for row in crisis_true_rows
            ],
        ),
        "",
    ]

    if intraday_rows:
        lines += [
            "## Key Result 2: Execution Assumptions Change Realized Exposure",
            "",
            _wrap(
                "The 51-stock hourly probe shows that low-liquidity and "
                "latency stress rows do not behave like ideal fills. Fill "
                "rate, rejected orders, and realized exposure become part of "
                "the benchmark outcome."
            ),
            "",
            "## 51-Stock Intraday Portfolio Probe",
            "",
            _wrap(
                "The intraday snapshot compares passive, deterministic, "
                "Markowitz/MVO, execution-stress, and redacted LLM policy "
                "rows on the same 51-stock hourly panel."
            ),
            "",
            _md_table(
                ["Agent / baseline", "Return", "Max drawdown", "Fill rate", "Rejected", "Risk edits", "Herfindahl", "Audit completeness"],
                [
                    [
                        _pretty_case(row["case"]),
                        _pct(float(row["total_return"])),
                        _pct(float(row["max_drawdown"])),
                        _pct(float(row["execution_fill_rate"])),
                        row["rejected_order_count"],
                        row["risk_clipped_decisions"],
                        f"{float(row['mean_herfindahl']):.3f}",
                        _pct(float(row["trajectory_reproducibility_coverage"])),
                    ]
                    for row in intraday_rows
                ],
            ),
            "",
        ]

    lines += [
        "## Key Result 3: Audit Completeness Is A Benchmark Dimension",
        "",
        _wrap(
            "Every result row should be traceable to a trajectory rather "
            "than only to a return curve. TradeArena therefore reports audit "
            "completeness and keeps compact, redacted result manifests."
        ),
        "",
        "## Representation Robustness Snapshot",
        "",
        _wrap(
            "A result is more useful when the diagnostic survives multiple "
            "representation views. The v0.1 tracked snapshot includes 80 "
            "rolling failure anchors and 320 pre-failure steps across eight "
            "LLM trajectories."
        ),
        "",
        _md_table(
            ["Embedding", "View", "Anchors", "Pre-failure steps", "Mean rank delta", "Contraction rate", "Mean pre-shift"],
            [
                [
                    row["embedding"],
                    row["view"],
                    str(row["anchors"]),
                    str(row["pre_steps"]),
                    f"{row['rank_delta']:.3f}",
                    _pct(row["contraction_rate"]),
                    f"{row['mean_pre_shift']:.3f}",
                ]
                for row in representation_summary
            ],
        ),
        "",
        "## Limitations",
        "",
        "- This is a benchmark and audit artifact, not financial advice.",
        "- It is not a live-trading system and does not promise profitability.",
        "- First-run reproduction uses tracked artifacts, not live provider calls.",
        "- Public rows use redacted or normalized policy labels.",
        "- Raw provider prompts, responses, credentials, and caches are not shipped.",
        "",
    ]
    return "\n".join(lines)


def _html(
    quickstart_rows: list[dict[str, Any]],
    crisis_summary: list[dict[str, Any]],
    crisis_true_rows: list[dict[str, str]],
    intraday_rows: list[dict[str, str]],
    representation_summary: list[dict[str, Any]],
) -> str:
    provenance = _provenance_rows()
    quickstart = ""
    if quickstart_rows:
        quickstart = _section(
            "First-Run Execution Benchmark",
            "Deterministic, local benchmark cases generated by the quickstart path.",
            _html_table(
                ["Scenario", "Agent / baseline", "Return", "Max drawdown", "Fill rate", "Rejection rate", "Risk edits", "Audit completeness"],
                [
                    [
                        row["scenario"],
                        row["agent"],
                        _pct(row["return"]),
                        _pct(row["max_drawdown"]),
                        _pct(row["fill_rate"]),
                        _pct(row["rejection_rate"]),
                        str(row["risk_edits"]),
                        _pct(row["audit_completeness"]),
                    ]
                    for row in quickstart_rows
                ],
            ),
        )

    crisis = _section(
        "Crisis-Scene LLM Benchmark",
        "Timestamp-masked 2022 Tech/Rates and 2023 SVB stress paths, averaged by feedback mode.",
        _html_table(
            ["Scenario", "Agent / baseline", "Return", "Max drawdown", "Fill rate", "Rejection rate", "Risk edits", "Audit completeness"],
            [
                [
                    row["scenario"],
                    row["agent"],
                    _pct(row["return"]),
                    _pct(row["max_drawdown"]),
                    _pct(row["fill_rate"]),
                    _pct(row["rejection_rate"]),
                    str(row["risk_edits"]),
                    _pct(row["audit_completeness"]),
                ]
                for row in crisis_summary
            ],
        ),
    )

    true_feedback = _section(
        "True-Feedback Model Rows",
        "Policy-level rows under structured true risk feedback. Model names are redacted or normalized labels; raw provider prompts and responses are not shipped.",
        _html_table(
            ["Scenario", "Policy label", "Return", "Max drawdown", "Fill rate", "Risk edits", "Violations", "Calibration"],
            [
                [
                    row["scene"],
                    _policy_label(row["model"]),
                    _pct(float(row["total_return"])),
                    _pct(float(row["max_drawdown"])),
                    _pct(float(row["execution_fill_rate"])),
                    row["risk_clipped_decisions"],
                    row["risk_violation_count"],
                    f"{float(row['mean_calibration_score']):.3f}",
                ]
                for row in crisis_true_rows
            ],
        ),
    )

    intraday = ""
    if intraday_rows:
        intraday = _section(
            "51-Stock Intraday Portfolio Probe",
            "Passive, deterministic, Markowitz/MVO, execution-stress, and redacted LLM policy rows on a 51-stock hourly panel.",
            _html_table(
                ["Agent / baseline", "Return", "Max drawdown", "Fill rate", "Rejected", "Risk edits", "Herfindahl", "Audit completeness"],
                [
                    [
                        _pretty_case(row["case"]),
                        _pct(float(row["total_return"])),
                        _pct(float(row["max_drawdown"])),
                        _pct(float(row["execution_fill_rate"])),
                        row["rejected_order_count"],
                        row["risk_clipped_decisions"],
                        f"{float(row['mean_herfindahl']):.3f}",
                        _pct(float(row["trajectory_reproducibility_coverage"])),
                    ]
                    for row in intraday_rows
                ],
            ),
        )

    representation = _section(
        "Representation Robustness Snapshot",
        "80 rolling failure anchors and 320 pre-failure steps across eight LLM trajectories.",
        _html_table(
            ["Embedding", "View", "Anchors", "Pre-failure steps", "Mean rank delta", "Contraction rate", "Mean pre-shift"],
            [
                [
                    row["embedding"],
                    row["view"],
                    str(row["anchors"]),
                    str(row["pre_steps"]),
                    f"{row['rank_delta']:.3f}",
                    _pct(row["contraction_rate"]),
                    f"{row['mean_pre_shift']:.3f}",
                ]
                for row in representation_summary
            ],
        ),
    )
    provenance_section = _section(
        "Result Provenance",
        "Where this benchmark card comes from and how to reproduce it.",
        _html_table(["Field", "Value"], provenance),
    )
    measured_section = _section(
        "What Is Measured",
        "The v0.1 card emphasizes audit and execution dimensions, not only return.",
        (
            "<ul>"
            "<li>Return and max drawdown.</li>"
            "<li>Fill rate, rejection rate, latency, slippage, and partial fills.</li>"
            "<li>Risk edits, clipped decisions, violations, and audit completeness.</li>"
            "<li>Concentration / Herfindahl for portfolio probes.</li>"
            "<li>Calibration and representation robustness diagnostics.</li>"
            "</ul>"
        ),
    )
    risk_gate_section = _section(
        "Key Result 1: Risk Gates Are Active, Not Cosmetic",
        "Risk gates repeatedly edit or clip intended allocations before execution.",
        '<p class="note">The benchmark reports risk edits alongside return so that risk control is visible in the result card.</p>',
    )
    execution_section = _section(
        "Key Result 2: Execution Assumptions Change Realized Exposure",
        "The 51-stock hourly probe separates intended allocation from realistic execution outcomes.",
        '<p class="note">Fill rate, rejected orders, latency, and slippage become part of the benchmark outcome.</p>',
    )
    audit_section = _section(
        "Key Result 3: Audit Completeness Is A Benchmark Dimension",
        "Each row should be traceable to a trajectory, not just a return curve.",
        (
            '<p class="note">TradeArena keeps compact result snapshots and redacted '
            "manifests so users can inspect what happened without shipping raw "
            "provider text.</p>"
        ),
    )

    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TradeArena v0.1 Benchmark Card</title>
<style>
body {{ margin: 0; font-family: Inter, Arial, sans-serif; color: #0f172a; background: #f8fafc; }}
main {{ max-width: 1180px; margin: 0 auto; padding: 42px 24px 58px; }}
a {{ color: #2563eb; }}
.hero {{ padding: 28px; background: #0f172a; color: #e2e8f0; border-radius: 12px; box-shadow: 0 22px 60px rgba(15, 23, 42, 0.18); }}
h1 {{ margin: 0 0 10px; font-size: 38px; letter-spacing: 0; }}
.lead {{ max-width: 900px; line-height: 1.56; color: #cbd5e1; margin: 0; }}
.links {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
.links a {{ padding: 8px 11px; border-radius: 8px; border: 1px solid #334155; color: #ccfbf1; background: #111827; text-decoration: none; font-weight: 800; font-size: 13px; }}
section {{ margin-top: 26px; padding: 20px; border: 1px solid #d8e2ed; border-radius: 10px; background: #fff; }}
h2 {{ margin: 0 0 6px; font-size: 24px; letter-spacing: 0; }}
.section-lead {{ margin: 0 0 14px; color: #64748b; line-height: 1.5; }}
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #e2e8f0; padding: 9px 8px; text-align: right; white-space: nowrap; }}
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
th {{ background: #f1f5f9; color: #334155; font-weight: 800; }}
.note {{ margin: 18px 0 0; color: #475569; line-height: 1.55; }}
code {{ background: #e2e8f0; border-radius: 5px; padding: 2px 5px; }}
</style>
<main>
  <div class="hero">
    <h1>TradeArena v0.1 Benchmark Card</h1>
    <p class="lead">Execution realism and risk gates materially change LLM trading-agent evaluation. This is a compact, citable result page for auditable agent evaluation, not a profitability claim or financial advice.</p>
    <div class="links">
      <a href="showcase.html">Showcase</a>
      <a href="audit_report.html">Audit report</a>
      <a href="crisis_snapshot_gallery.html">Crisis gallery</a>
      <a href="https://github.com/weich97/TradeArena">GitHub</a>
    </div>
  </div>
  {provenance_section}
  {measured_section}
  {quickstart}
  {risk_gate_section}
  {crisis}
  {true_feedback}
  {execution_section}
  {intraday}
  {audit_section}
  {representation}
  <section>
    <h2>Limitations</h2>
    <p class="note">This page is a benchmark and audit artifact, not financial advice or a live-trading guarantee. First-run reproduction uses tracked artifacts, and public policy rows use redacted or normalized labels. Raw provider prompts, responses, credentials, and caches are not shipped.</p>
  </section>
</main>
</html>
"""


def _section(title: str, lead: str, body: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2><p class=\"section-lead\">{html.escape(lead)}</p>{body}</section>"


def _html_table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    body = "\n".join("<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def _provenance_rows() -> list[list[str]]:
    return [
        ["Release", RELEASE_TAG],
        ["Release commit", RELEASE_COMMIT],
        ["Benchmark card source", "`docs/results/` tracked snapshots plus first-run outputs"],
        [
            "Reproduction command",
            "`python -m pip install -e \".[dev]\"`; `python scripts/run_showcase.py`; `python scripts/build_benchmark_page.py`",
        ],
        ["Data", "tracked synthetic / timestamp-masked / redacted artifacts under `docs/results/`"],
        ["Live model calls", "not required for first-run reproduction"],
        ["Raw prompt/response caches", "not included"],
        ["Intended use", "benchmark and audit research, not trading advice"],
    ]


def _mean(rows: list[dict[str, str]], field: str) -> float:
    return statistics.fmean(float(row[field]) for row in rows)


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def _policy_label(model: str) -> str:
    return POLICY_LABELS.get(model, "frontier-policy (redacted)")


def _wrap(text: str) -> str:
    return textwrap.fill(text, width=88)


def _pretty_case(case: str) -> str:
    text = case.replace("intraday_50_", "").replace("_risk_aware", "").replace("_", " ")
    replacements = {
        "buy and hold": "Buy and Hold",
        "deterministic": "Deterministic Risk-Aware",
        "markowitz mvo": "Markowitz MVO",
        "low liquidity stress": "Low-Liquidity Stress",
        "latency stress": "Latency Stress",
        "llm gpt 5 5": "Frontier Policy A (redacted)",
        "llm gemini 3 1 pro": "Frontier Policy C (redacted)",
    }
    for needle, label in replacements.items():
        if text.startswith(needle):
            return label
    return text.title()


if __name__ == "__main__":
    raise SystemExit(main())
