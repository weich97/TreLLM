from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs/examples"


SECTIONS = [
    (
        "First-run portal",
        "A guided API-free tour of the audit report, A-share rules, crisis gallery, and redacted cache manifest.",
        "index.html",
        "python scripts/run_launch_demo.py",
    ),
    (
        "Experiment-design demos",
        "Execution realism, Markowitz/MVO baselines, representation signatures, and custom plugin extensibility.",
        "experiment_design_index.html",
        "python scripts/run_paper_design_demos.py",
    ),
    (
        "Animated visual tour",
        "A hands-on regeneration of the audit lifecycle, execution realism, and diagnostics GIFs shown in the README.",
        "visual_tour_index.html",
        "python examples/visual_tour_demo.py",
    ),
    (
        "Audit report",
        "One complete observe-plan-risk-act-reflect trajectory with risk gate and execution outcomes.",
        "audit_report.html",
        "python scripts/render_audit_report.py",
    ),
    (
        "Crisis gallery",
        "Representation trajectory, correlation/intent heatmap, feedback curves, and exposure waterfall snapshots.",
        "crisis_snapshot_gallery.html",
        "python examples/crisis_snapshot_demo.py",
    ),
    (
        "A-share rule stress",
        "T+1, price-limit, and board-lot constraints as auditable risk-gate interventions.",
        "ashare_market_rules.svg",
        "python examples/ashare_market_rules_demo.py",
    ),
    (
        "Custom plugin extension",
        "A local analyst plugin running through the same strategy, risk, execution, memory, and evaluator stack.",
        "custom_plugin.svg",
        "python examples/custom_plugin_demo.py",
    ),
    (
        "Contributor extension walkthrough",
        "Swap in a custom analyst, risk manager, and evaluator while reusing the rest of the framework.",
        "extension_walkthrough.svg",
        "python examples/extension_walkthrough_demo.py",
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the public-facing TradeArena showcase.")
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Only write the showcase index from existing artifacts; do not rerun demos.",
    )
    args = parser.parse_args()

    print("TradeArena showcase", flush=True)
    print("===================", flush=True)
    print("A one-command API-free repo tour for new users, reviewers, and launch posts.", flush=True)

    if not args.reuse_existing:
        _run([sys.executable, "scripts/run_launch_demo.py", "--skip-paper-figures"], "Launch demo portal")
        _run([sys.executable, "scripts/run_paper_design_demos.py"], "Experiment-design demo suite")
        _run([sys.executable, "examples/visual_tour_demo.py"], "Animated visual tour")
        _run([sys.executable, "examples/extension_walkthrough_demo.py"], "Contributor extension walkthrough")

    _write_showcase_index(OUTPUT_DIR / "showcase.html")
    print("\nShowcase artifacts", flush=True)
    print("------------------", flush=True)
    for _, _, href, _ in SECTIONS:
        path = OUTPUT_DIR / href
        print(f"[{'ok' if path.exists() else 'missing'}] outputs/examples/{href}", flush=True)
    print("[ok] outputs/examples/showcase.html", flush=True)
    return 0


def _run(command: list[str], label: str) -> None:
    print(f"\n{label}", flush=True)
    print("-" * len(label), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def _write_showcase_index(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cards = "\n".join(_card_html(title, body, href, command) for title, body, href, command in SECTIONS)
    html = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>TradeArena Showcase</title>
<style>
body {{ margin: 0; font-family: Inter, Arial, sans-serif; background: #f8fafc; color: #0f172a; }}
main {{ max-width: 1080px; margin: 0 auto; padding: 44px 28px 54px; }}
h1 {{ margin: 0 0 8px; font-size: 36px; letter-spacing: 0; }}
.lead {{ margin: 0 0 18px; max-width: 820px; color: #475569; line-height: 1.58; }}
.strip {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 26px; }}
.pill {{ border: 1px solid #cbd5e1; border-radius: 999px; padding: 6px 10px; background: #ffffff; color: #334155; font-size: 12px; font-weight: 700; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 14px; }}
.card {{ display: block; min-height: 154px; padding: 18px; border: 1px solid #d8e2ed; border-radius: 8px; background: white; color: inherit; text-decoration: none; }}
.card:hover {{ border-color: #2563eb; box-shadow: 0 12px 28px rgba(15, 23, 42, 0.10); transform: translateY(-1px); }}
.card span {{ display: block; font-weight: 800; font-size: 16px; margin-bottom: 8px; }}
.card p {{ margin: 0 0 12px; color: #64748b; font-size: 13px; line-height: 1.45; }}
.command {{ display: inline-block; padding: 6px 8px; border-radius: 6px; background: #f1f5f9; color: #334155; font-size: 12px; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }}
.footer {{ margin-top: 26px; color: #64748b; font-size: 13px; line-height: 1.5; }}
</style>
<main>
  <h1>TradeArena Showcase</h1>
  <p class="lead">A compact, API-free launch surface for the repository: run one command, open one page, then inspect the artifacts that demonstrate auditable trajectories, realistic execution, risk gates, diagnostic visuals, and extensible plugins.</p>
  <div class="strip">
    <span class="pill">No API key required</span>
    <span class="pill">Execution realism</span>
    <span class="pill">Risk lifecycle</span>
    <span class="pill">Replayable trajectories</span>
    <span class="pill">Extensible plugins</span>
  </div>
  <section class="grid">
    {cards}
  </section>
  <p class="footer">Generated by <code>python scripts/run_showcase.py</code>. Large model calls and live market-data downloads are intentionally outside the first-run path.</p>
</main>
</html>
"""
    path.write_text(html, encoding="utf-8")
    print(f"\nWrote {path.relative_to(ROOT)}", flush=True)


def _card_html(title: str, body: str, href: str, command: str) -> str:
    status = "ready" if (OUTPUT_DIR / href).exists() else "generate first"
    return (
        f'<a class="card" href="{href}">'
        f"<span>{title}</span>"
        f"<p>{body}</p>"
        f'<code class="command">{command}</code>'
        f'<p style="margin-top:10px">Artifact status: {status}</p>'
        "</a>"
    )


if __name__ == "__main__":
    raise SystemExit(main())
